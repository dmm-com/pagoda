from typing import Any, Dict, List, Optional, TypedDict

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from acl.models import ACLBase
from airone.lib.acl import ACLObjType, ACLType
from airone.lib.drf import IncorrectTypeError, ObjectNotExistsError, RequiredParameterError
from entity.models import Entity, EntityAttr
from entry.models import Attribute, Entry
from role.models import HistoricalPermission, Role
from user.models import User


class ACLParentType(TypedDict):
    id: int
    name: str
    is_public: bool


class ACLRoleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    current_permission = serializers.IntegerField()

    class ACLRoleType(TypedDict):
        id: int
        name: str
        description: str
        current_permission: int


class ACLRoleListSerializer(serializers.ListSerializer):
    child = ACLRoleSerializer()


class ACLSerializer(serializers.ModelSerializer):
    @extend_schema_field(
        {
            "type": "integer",
            "enum": [k.value for k in ACLObjType],
            "x-enum-varnames": [k.name for k in ACLObjType],
        }
    )
    class ObjTypeField(serializers.IntegerField):
        pass

    parent = serializers.SerializerMethodField(method_name="get_parent", read_only=True)
    roles = serializers.SerializerMethodField(method_name="get_roles", read_only=True)
    # TODO better name?
    acl = serializers.ListField(write_only=True, required=False)
    objtype = ObjTypeField(read_only=True)

    class Meta:
        model = ACLBase
        fields = [
            "id",
            "name",
            "is_public",
            "default_permission",
            "objtype",
            "acl",
            "roles",
            "parent",
        ]

        extra_kwargs = {
            "name": {"read_only": True},
        }

    def get_parent(self, obj: ACLBase) -> Optional[ACLParentType]:
        airone_model = obj.get_subclass_object()
        if isinstance(airone_model, Entry):
            return {
                "id": airone_model.schema.id,
                "name": airone_model.schema.name,
                "is_public": airone_model.schema.is_public,
            }
        if isinstance(airone_model, Attribute):
            return {
                "id": airone_model.parent_entry.id,
                "name": airone_model.parent_entry.name,
                "is_public": airone_model.parent_entry.is_public,
            }
        elif isinstance(airone_model, EntityAttr):
            return {
                "id": airone_model.parent_entity.id,
                "name": airone_model.parent_entity.name,
                "is_public": airone_model.parent_entity.is_public,
            }
        else:
            return None

    @extend_schema_field(ACLRoleListSerializer)
    def get_roles(self, obj: ACLBase) -> List[ACLRoleSerializer.ACLRoleType]:
        user = self.context["request"].user

        return [
            {
                "id": x.id,
                "name": x.name,
                "description": x.description,
                "current_permission": x.get_current_permission(obj),
            }
            for x in Role.objects.filter(is_active=True)
            if user.is_superuser or x.is_belonged_to(user)
        ]

    def validate_default_permission(self, default_permission: int):
        if default_permission not in ACLType.all():
            raise IncorrectTypeError("invalid default_permission parameter")
        return default_permission

    def validate(self, attrs: Dict[str, Any]):
        # validate acl paramter
        for acl_info in attrs.get("acl", []):
            if "member_id" not in acl_info:
                raise RequiredParameterError(
                    '"member_id" parameter is necessary for "acl" parameter'
                )

            role = Role.objects.filter(id=acl_info["member_id"]).first()
            if not role:
                raise ObjectNotExistsError("Invalid member_id of Role instance is specified")

        acl: ACLBase = self.instance
        user: User = self.context["request"].user
        if not user.is_permitted_to_change(
            acl,
            ACLType.Full,
            **{
                "will_be_public": attrs.get("is_public", acl.is_public),
                "default_permission": attrs.get("default_permission", acl.default_permission),
                "acl_settings": [
                    {
                        "role": Role.objects.filter(id=x["member_id"], is_active=True).first(),
                        "value": int(x["value"]),
                    }
                    for x in attrs.get("acl", [])
                ]
                + [
                    {"role": role, "value": ACLType.Full}
                    for role in acl.full.roles.exclude(
                        id__in=[x["member_id"] for x in attrs.get("acl", [])]
                    )
                ],
            }
        ):
            raise PermissionDenied(
                "Inadmissible setting. By this change you will never change this ACL"
            )

        return attrs

    def update(self, instance: ACLBase, validated_data):
        obj = instance.get_subclass_object()
        if "is_public" in validated_data and validated_data["is_public"] != obj.is_public:
            obj.is_public = validated_data["is_public"]

        if (
            "default_permission" in validated_data
            and validated_data["default_permission"] != obj.default_permission
        ):
            obj.default_permission = validated_data["default_permission"]

        obj.save()

        permissions = {}
        for permission in HistoricalPermission.objects.filter(
            codename__startswith="%s." % instance.id
        ):
            permissions[permission.name] = permission

        for item in [x for x in validated_data.get("acl", []) if x["value"]]:
            role = Role.objects.get(id=item["member_id"])
            acl_type = [x for x in ACLType.all() if x == int(item["value"])][0]

            # update permissios for the target ACLBased object
            self._set_permission(role, instance, permissions, acl_type)

        return instance

    @staticmethod
    def _get_acl_model(object_id):
        if int(object_id) == ACLObjType.Entity:
            return Entity
        if int(object_id) == ACLObjType.Entry:
            return Entry
        elif int(object_id) == ACLObjType.EntityAttr:
            return EntityAttr
        elif int(object_id) == ACLObjType.EntryAttr:
            return Attribute
        else:
            return ACLBase

    @staticmethod
    def _set_permission(
        role: Role, acl_obj: ACLBase, permissions: Dict[str, HistoricalPermission], acl_type
    ):
        # clear unset permissions of target ACLbased object
        permission: HistoricalPermission
        for permission in role.permissions.filter(codename__startswith="%s." % acl_obj.id):
            if acl_type == ACLType.Nothing:
                permission.roles.remove(role)
            if acl_type.name != permission.name:
                permission.roles.remove(role)

        # set new permission to be specified except for 'Nothing' permission
        if acl_type != ACLType.Nothing:
            permission = permissions[acl_type.name]
            permission.roles.add(role)


class ACLHistoryUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()


class ACLHistoryChangeSerializer(serializers.Serializer):
    # unkwnon | create | update | delete
    action = serializers.CharField()
    # is_public | default_permission | <role name>
    target = serializers.CharField()
    before = serializers.SerializerMethodField(required=False)
    after = serializers.SerializerMethodField(required=False)

    def get_before(self, change) -> Any:
        return change.before

    def get_after(self, change) -> Any:
        return change.after


class ACLHistorySerializer(serializers.Serializer):
    user = ACLHistoryUserSerializer(source="history_user")
    time = serializers.DateTimeField(source="history_date")
    name = serializers.SerializerMethodField()
    changes = serializers.SerializerMethodField()

    @extend_schema_field(str)
    def get_name(self, history):
        if history.__class__.__name__ == "HistoricalHistoricalPermission":
            obj = ACLBase.objects.filter(id=history.codename.split(".")[0]).first()
            return obj.name if obj else ""
        else:
            return history.name

    @extend_schema_field(ACLHistoryChangeSerializer(many=True))
    def get_changes(self, history):
        if history.__class__.__name__ == "HistoricalHistoricalPermission":
            if history.prev_record:
                delta = history.diff_against(history.prev_record, excluded_fields=["status"])
                if "roles" not in delta.changed_fields:
                    return []

                before = {r.id: r for r in history.prev_record.roles.all()}
                after = {r.id: r for r in history.roles.all()}
                return [
                    {
                        "action": "delete",
                        "target": before[key].role.name,
                        "before": self._acl_id(history.codename),
                        "after": ACLType.Nothing.id,
                    }
                    for key in set(before.keys()) - set(after.keys())
                ] + [
                    {
                        "action": "create",
                        "target": after[key].role.name,
                        "before": ACLType.Nothing.id,
                        "after": self._acl_id(history.codename),
                    }
                    for key in set(after.keys()) - set(before.keys())
                ]
            else:
                return []
        else:
            if history.prev_record:
                delta = history.diff_against(history.prev_record, excluded_fields=["status"])
                return [
                    {
                        "action": "update",
                        "target": change.field,
                        "before": change.old,
                        "after": change.new,
                    }
                    for change in delta.changes
                    if change.field in ["is_public", "default_permission"]
                ]
            else:
                return [
                    {
                        "action": "create",
                        "target": field,
                        "before": None,
                        "after": getattr(history, field),
                    }
                    for field in ["is_public", "default_permission"]
                    if hasattr(history, field)
                ]

    def _acl_id(self, codename: str) -> int:
        return int(codename.split(".")[1])
