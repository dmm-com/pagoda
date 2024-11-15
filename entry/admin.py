from django.contrib import admin
from import_export import fields, widgets
from import_export.admin import ImportExportModelAdmin
from import_export.instance_loaders import CachedInstanceLoader

from acl.models import ACLBase
from airone.lib.resources import AironeModelResource
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from user.models import User

from .models import Attribute, AttributeValue, Entry

admin.site.register(Entry)
admin.site.register(Attribute)
admin.site.register(AttributeValue)


class AttrValueResource(AironeModelResource):
    _IMPORT_INFO = {
        "header": [
            "id",
            "refer",
            "value",
            "attribute_id",
            "created_time",
            "created_user",
            "status",
            "parent_attrv",
        ],
        "mandatory_keys": ["id", "attribute_id", "created_user", "status"],
        "resource_module": "entry.admin",
        "resource_model_name": "AttrValueResource",
    }
    COMPARING_KEYS = []
    DISALLOW_UPDATE_KEYS = [
        "created_time",
        "created_user",
        "parent_attr",
        "value",
        "referral",
        "status",
    ]

    attr_id = fields.Field(
        column_name="attribute_id",
        attribute="parent_attr",
        widget=widgets.ForeignKeyWidget(model=Attribute, field="id"),
    )
    refer = fields.Field(
        column_name="refer",
        attribute="referral",
        widget=widgets.ForeignKeyWidget(model=ACLBase, field="id"),
    )
    user = fields.Field(
        column_name="created_user",
        attribute="created_user",
        widget=widgets.ForeignKeyWidget(User, "username"),
    )
    parent_attrv = fields.Field(
        column_name="parent_attrv",
        attribute="parent_attrv",
        widget=widgets.ForeignKeyWidget(AttributeValue, "id"),
    )

    class Meta:
        model = AttributeValue
        fields = ("id", "name", "value", "created_time", "status")
        skip_unchanged = True
        instance_loader_class = CachedInstanceLoader

    def after_save_instance(self, instance, using_transactions, dry_run):
        # If a new AttributeValue object is created,
        # this processing append it to the associated Entity object.
        self._saved_instance = None
        if not dry_run:
            attr = instance.parent_attr

            # register data_type parameter which is same with EntityAttr's type
            instance.data_type = attr.schema.type

            if not attr.values.filter(id=instance.id).exists() and (
                not attr.schema.type & AttrType._ARRAY
                or (
                    attr.schema.type & AttrType._ARRAY
                    and instance.get_status(AttributeValue.STATUS_DATA_ARRAY_PARENT)
                )
            ):
                # clear is_latest flag of old attrs and set it to new one.
                instance.is_latest = True
                attr.values.add(instance)
                attr.unset_latest_flag(exclude_id=instance.id)

            # the case of leaf AttributeValue
            elif attr.schema.type & AttrType._ARRAY and not instance.get_status(
                AttributeValue.STATUS_DATA_ARRAY_PARENT
            ):
                # For a leaf AttributeValue, 'is_latest' flag will not be set.
                # Instaed, these objects have
                # parent_attrv parameter to identify parent AttributeValue.
                instance.is_latest = False
                instance.parent_attrv = attr.get_latest_value()

            instance.save(update_fields=["is_latest", "data_type", "parent_attrv"])
            self._saved_instance = instance
            attr.parent_entry.register_es()

    @classmethod
    def after_import_completion(self, results):
        # make relation between the array of AttributeValue
        for data in [
            x["data"]
            for x in results
            if x["data"]["status"] & AttributeValue.STATUS_DATA_ARRAY_PARENT
        ]:
            attr_value = AttributeValue.objects.get(id=data["id"])
            attr_value.parent_attr.parent_entry.register_es()


class AttrResource(AironeModelResource):
    _IMPORT_INFO = {
        "header": ["id", "name", "schema_id", "entry_id", "created_user"],
        "mandatory_keys": ["name", "schema_id", "entry_id", "created_user"],
        "resource_module": "entry.admin",
        "resource_model_name": "AttrResource",
    }
    COMPARING_KEYS = ["name", "created_user"]
    DISALLOW_UPDATE_KEYS = ["created_user"]

    entry = fields.Field(
        column_name="entry_id",
        attribute="parent_entry",
        widget=widgets.ForeignKeyWidget(model=Entry, field="id"),
    )
    schema = fields.Field(
        column_name="schema_id",
        attribute="schema",
        widget=widgets.ForeignKeyWidget(model=EntityAttr, field="id"),
    )
    user = fields.Field(
        column_name="created_user",
        attribute="created_user",
        widget=widgets.ForeignKeyWidget(User, "username"),
    )

    class Meta:
        model = Attribute
        fields = ("id", "name", "schema_id")
        skip_unchanged = True
        instance_loader_class = CachedInstanceLoader

    def after_save_instance(self, instance, using_transactions, dry_run):
        # If a new Attribute object is created,
        # this processing append it to the associated Entity object.
        if not dry_run:
            entry = instance.parent_entry

            if not entry.attrs.filter(id=instance.id).exists():
                entry.register_es()


class EntryResource(AironeModelResource):
    _IMPORT_INFO = {
        "header": ["id", "name", "entity", "created_user"],
        "mandatory_keys": ["name", "entity", "created_user"],
        "mandatory_values": ["name"],
        "resource_module": "entry.admin",
        "resource_model_name": "EntryResource",
    }
    COMPARING_KEYS = ["name"]

    entity = fields.Field(
        column_name="entity",
        attribute="schema",
        widget=widgets.ForeignKeyWidget(model=Entity, field="name"),
    )
    user = fields.Field(
        column_name="created_user",
        attribute="created_user",
        widget=widgets.ForeignKeyWidget(User, "username"),
    )

    class Meta:
        model = Entry
        fields = ("id", "name")
        skip_unchanged = True
        instance_loader_class = CachedInstanceLoader

    def import_obj(self, instance, data, dry_run, **kwargs):
        # will not import entry which refers invalid entity
        if not Entity.objects.filter(name=data["entity"]).exists():
            raise RuntimeError("Specified entity(%s) doesn't exist" % data["entity"])

        # will not import entry which has same name and refers same entity
        entity = Entity.objects.get(name=data["entity"])
        if Entry.objects.filter(schema=entity, name=data["name"]).exists():
            entry = Entry.objects.get(schema=entity, name=data["name"])
            if "id" not in data or not data["id"] or entry.id != data["id"]:
                raise RuntimeError("There is a duplicate entry object")

        super(EntryResource, self).import_obj(instance, data, dry_run, **kwargs)

    def after_save_instance(self, instance, using_transactions, dry_run):
        if not dry_run:
            # register imported entry to the Elasticsearch
            instance.register_es()


class EntryAdmin(ImportExportModelAdmin):
    resource_class = EntryResource
    skip_admin_log = True


class AttrAdmin(ImportExportModelAdmin):
    resource_class = AttrResource
    skip_admin_log = True


class AttrValueAdmin(ImportExportModelAdmin):
    resource_class = AttrValueResource
    skip_admin_log = True
