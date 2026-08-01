from typing import Any

from django.contrib import admin
from import_export import fields, widgets

from airone.lib import custom_view
from airone.lib.resources import AironeModelResource
from user.models import User

from .models import Entity, EntityAttr

admin.site.register(EntityAttr)
admin.site.register(Entity)


def check_entity_row(row: dict[str, Any], known_entity_names: set[str] | None = None) -> None:
    """Reject an Entity row the import could not accept. Raises RuntimeError.

    ``known_entity_names`` lets a caller treat models as existing that do not
    exist yet -- the import preview uses it for models the same file creates.
    """
    duplicated = Entity.objects.filter(name=row["name"]).first()
    if duplicated and ("id" not in row or not row["id"] or duplicated.id != int(row["id"])):
        raise RuntimeError("There is a duplicate entity object (%s)" % row["name"])


def check_entity_attr_row(
    row: dict[str, Any], is_new: bool, known_entity_names: set[str] | None = None
) -> None:
    """Reject an EntityAttr row the import could not accept. Raises RuntimeError."""
    known = known_entity_names or set()

    def _exists(name: str) -> bool:
        return name in known or Entity.objects.filter(name=name).exists()

    if not _exists(row["entity"]):
        raise RuntimeError("failed to identify entity object")

    if row["refer"] and not all([_exists(x) for x in row["refer"].split(",")]):
        raise RuntimeError("refer to invalid entity object")

    # The processing fails when 'type' parameter is not existed for creating a new instance
    if is_new and not row["type"]:
        raise RuntimeError("The parameter 'type' is mandatory when a new EntityAtter create")


class EntityResource(AironeModelResource):
    _IMPORT_INFO = {
        "header": ["id", "name", "note", "created_user", "status"],
        "mandatory_keys": ["name", "created_user"],
        "resource_module": "entity.admin",
        "resource_model_name": "EntityResource",
    }

    COMPARING_KEYS = ["name", "note", "created_user", "status"]
    DISALLOW_UPDATE_KEYS = ["created_user"]

    user = fields.Field(
        column_name="created_user",
        attribute="created_user",
        widget=widgets.ForeignKeyWidget(User, "username"),
    )

    class Meta:
        model = Entity
        fields = ("id", "name", "note", "status", "user")
        export_order = ("id", "name", "note", "user")

    def import_instance(self, instance: Entity, row: dict[str, Any], **kwargs: Any) -> None:
        check_entity_row(row)

        # Set event handler for custom-view. When it returns not None, then it abort to import.
        if custom_view.is_custom("import_entity"):
            error = custom_view.call_custom("import_entity", None, instance, row)
            if error:
                raise RuntimeError(error)

        super().import_instance(instance, row, **kwargs)


class EntityAttrResource(AironeModelResource):
    _IMPORT_INFO = {
        "header": [
            "id",
            "name",
            "type",
            "refer",
            "entity",
            "created_user",
            "is_mandatory",
        ],
        "mandatory_keys": ["name", "entity", "created_user"],
        "resource_module": "entity.admin",
        "resource_model_name": "EntityAttrResource",
    }

    COMPARING_KEYS = [
        "name",
        "is_mandatory",
        "referral",
        "parent_entity",
        "created_user",
    ]
    DISALLOW_UPDATE_KEYS = ["parent_entity", "created_user"]

    user = fields.Field(
        column_name="created_user",
        attribute="created_user",
        widget=widgets.ForeignKeyWidget(User, "username"),
    )
    refer = fields.Field(
        column_name="refer",
        attribute="referral",
        widget=widgets.ManyToManyWidget(model=Entity, field="name"),
    )
    entity = fields.Field(
        column_name="entity",
        attribute="parent_entity",
        widget=widgets.ForeignKeyWidget(model=Entity, field="name"),
    )

    class Meta:
        model = EntityAttr
        fields = ("id", "name", "type", "is_mandatory", "user", "refer", "entity")

    def import_instance(self, instance: EntityAttr, row: dict[str, Any], **kwargs: Any) -> None:
        check_entity_attr_row(row, is_new=not instance.pk)

        # Set event handler for custom-view. When it returns not None, then it abort to import.
        if custom_view.is_custom("import_entity_attr"):
            error = custom_view.call_custom("import_entity_attr", None, instance, row)
            if error:
                raise RuntimeError(error)

        # Do not allow to change type when instance is already created
        if instance.pk:
            row["type"] = instance.type

        super().import_instance(instance, row, **kwargs)
