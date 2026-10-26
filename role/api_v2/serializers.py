from collections import OrderedDict
from typing import Any, cast

from django.conf import settings
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from acl.models import ACLBase
from airone.lib.drf import RequiredParameterError
from group.models import Group
from role.models import Role
from user.models import User


class RoleUserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
        ]


class RoleGroupSerializer(serializers.ModelSerializer[Group]):
    class Meta:
        model = Group
        fields = [
            "id",
            "name",
        ]


class RolePermissionSerializer(serializers.Serializer[Any]):
    type = serializers.CharField()
    id = serializers.IntegerField()
    model_name = serializers.CharField()
    name = serializers.CharField()
    permission = serializers.CharField()


class RoleSerializer(serializers.ModelSerializer[Role]):
    users = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    admin_users = serializers.SerializerMethodField()
    admin_groups = serializers.SerializerMethodField()
    is_editable = serializers.SerializerMethodField(method_name="get_is_editable", read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            "id",
            "is_active",
            "name",
            "description",
            "users",
            "groups",
            "admin_users",
            "admin_groups",
            "is_editable",
            "permissions",
        ]

    @extend_schema_field(RoleUserSerializer(many=True))
    def get_users(self, obj: Role) -> list[dict[str, Any]]:
        return RoleUserSerializer(obj.users.all(), many=True).data  # type: ignore[return-value]

    @extend_schema_field(RoleUserSerializer(many=True))
    def get_admin_users(self, obj: Role) -> list[dict[str, Any]]:
        return RoleUserSerializer(obj.admin_users.all(), many=True).data  # type: ignore[return-value]

    @extend_schema_field(RoleGroupSerializer(many=True))
    def get_groups(self, obj: Role) -> list[dict[str, Any]]:
        return RoleGroupSerializer(obj.groups.all(), many=True).data  # type: ignore[return-value]

    @extend_schema_field(RoleGroupSerializer(many=True))
    def get_admin_groups(self, obj: Role) -> list[dict[str, Any]]:
        return RoleGroupSerializer(obj.admin_groups.all(), many=True).data  # type: ignore[return-value]

    def get_is_editable(self, obj: Role) -> bool:
        current_user = cast(User, self.context["request"].user)
        return Role.editable(
            current_user, list(obj.admin_users.all()), list(obj.admin_groups.all())
        )

    @extend_schema_field(RolePermissionSerializer(many=True))
    def get_permissions(self, obj: Role) -> list[dict[str, Any]]:
        permissions = list(obj.permissions.all())
        permission_obj_ids = [
            permission.get_objid()  # type: ignore[attr-defined]
            for permission in permissions
        ]
        objects = ACLBase.objects.in_bulk(permission_obj_ids)
        result = []
        for permission, obj_id in zip(permissions, permission_obj_ids, strict=True):
            acl_object = objects.get(obj_id)
            if acl_object is None or not acl_object.is_active:
                continue
            target = cast(Any, acl_object.get_subclass_object())
            model_name = "-"
            match type(target).__name__:
                case "EntityAttr":
                    model_name = target.parent_entity.name
                case "Entry":
                    model_name = target.schema.name
                case "Attribute":
                    model_name = target.schema.parent_entity.name
            result.append(
                {
                    "type": type(target).__name__,
                    "id": target.pk,
                    "model_name": model_name,
                    "name": target.name,
                    "permission": permission.name,
                }
            )
        return result


class RoleCreateUpdateSerializer(serializers.ModelSerializer[Role]):
    class Meta:
        model = Role
        fields = [
            "is_active",
            "name",
            "description",
            "users",
            "groups",
            "admin_users",
            "admin_groups",
        ]

    def validate(self, role: OrderedDict[str, Any]) -> OrderedDict[str, Any]:
        if not role.get("admin_users") and not role.get("admin_groups"):
            raise RequiredParameterError("admin_users or admin_groups field is required")

        users: list[User] = role.get("users", [])
        groups: list[Group] = role.get("groups", [])
        admin_users: list[User] = role.get("admin_users", [])
        admin_groups: list[Group] = role.get("admin_groups", [])

        user = cast(User, self.context["request"].user)
        if not Role.editable(user, admin_users, cast(list[Any], admin_groups)):
            raise RequiredParameterError(
                "your account must be set as a member of admin_users or admin_groups"
            )

        duplicate_user_names = set([x.username for x in users]) & set(
            [x.username for x in admin_users]
        )
        if duplicate_user_names:
            raise RequiredParameterError(
                "following users are duplicated: %s" % ", ".join(duplicate_user_names)
            )

        duplicate_group_names = set([x.name for x in groups]) & set([x.name for x in admin_groups])
        if duplicate_group_names:
            raise RequiredParameterError(
                "following groups are duplicated: %s" % ", ".join(duplicate_group_names)
            )

        return role


class RoleImportExportChildSerializer(serializers.ModelSerializer[Role]):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField()
    users = serializers.ListField(child=serializers.CharField())
    groups = serializers.ListField(child=serializers.CharField())
    admin_users = serializers.ListField(child=serializers.CharField())
    admin_groups = serializers.ListField(child=serializers.CharField())
    permissions = serializers.ListField(required=False, child=serializers.DictField())

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "description",
            "users",
            "groups",
            "admin_users",
            "admin_groups",
            "permissions",
        ]

    def validate(self, role: OrderedDict[str, Any]) -> OrderedDict[str, Any]:
        errors: dict[str, list[str]] = {}
        model_fields: list[tuple[str, Any, str]] = [
            ("users", User, "username"),
            ("admin_users", User, "username"),
            ("groups", Group, "name"),
            ("admin_groups", Group, "name"),
        ]
        for key, model, field in model_fields:
            missing = [
                name
                for name in role.get(key, [])
                if not model.objects.filter(**{field: name, "is_active": True}).exists()
            ]
            if missing:
                errors[key] = ["specified object is not found: " + ", ".join(missing)]
        invalid = [
            str(permission.get("obj_id"))
            for permission in role.get("permissions", [])
            if permission.get("permission") not in {"readable", "writable", "full"}
            or not ACLBase.objects.filter(id=permission.get("obj_id")).exists()
        ]
        if invalid:
            errors["permissions"] = ["invalid permission object: " + ", ".join(invalid)]
        if errors:
            raise serializers.ValidationError(errors)
        return role

    def to_representation(self, instance: Role) -> dict[str, Any]:
        def _get_permission_data(permission_obj: Any) -> dict[str, Any]:
            return {
                "obj_id": permission_obj.get_objid(),
                "permission": permission_obj.name,
            }

        return {
            "id": instance.id,
            "name": instance.name,
            "description": instance.description,
            "users": [x.username for x in instance.users.filter(is_active=True)],
            "groups": [x.name for x in instance.groups.filter(is_active=True)],
            "admin_users": [x.username for x in instance.admin_users.filter(is_active=True)],
            "admin_groups": [x.name for x in instance.admin_groups.filter(is_active=True)],
            "permissions": [_get_permission_data(x) for x in instance.permissions.all()],
        }


class RoleImportSerializer(serializers.ListSerializer[Role]):
    child = RoleImportExportChildSerializer()

    def validate(self, roles: list[OrderedDict[str, Any]]) -> list[OrderedDict[str, Any]]:
        errors: list[str] = []
        names: dict[str, int] = {}
        new_role_count = 0

        for index, role_data in enumerate(roles):
            name = role_data["name"]
            names[name] = names.get(name, 0) + 1
            role_id = role_data.get("id")
            role_id = cast(int, role_id) if role_id is not None else None
            role = Role.objects.filter(id=role_id).first() if role_id is not None else None

            if role_id is not None and role is None:
                errors.append(f"role id {role_id} does not exist")
                continue

            conflicting = Role.objects.filter(name=name)
            if role_id is not None:
                conflicting = conflicting.exclude(id=role_id)
            if conflicting.exists():
                errors.append(f"roles[{index}]: role name '{name}' is already used")
            if role_id is None and not Role.objects.filter(name=name).exists():
                new_role_count += 1

        duplicate_names = [name for name, count in names.items() if count > 1]
        if duplicate_names:
            errors.append("duplicate role names: " + ", ".join(duplicate_names))

        max_roles = settings.MAX_ROLES
        if max_roles and Role.objects.count() + new_role_count > max_roles:
            errors.append("The number of roles is over the limit")

        if errors:
            raise serializers.ValidationError({"roles": errors})
        return roles
