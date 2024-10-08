from collections import OrderedDict

from rest_framework import serializers

from airone.lib.drf import RequiredParameterError
from group.models import Group
from role.models import Role
from user.models import User


class RoleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
        ]


class RoleGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "name",
        ]


class RoleSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    admin_users = serializers.SerializerMethodField()
    admin_groups = serializers.SerializerMethodField()
    is_editable = serializers.SerializerMethodField(method_name="get_is_editable", read_only=True)

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
        ]

    def get_filtered_data(self, obj, attribute, serializer):
        return serializer(getattr(obj, attribute).filter(is_active=True), many=True).data

    def get_users(self, obj):
        return self.get_filtered_data(obj, "users", RoleUserSerializer)

    def get_admin_users(self, obj):
        return self.get_filtered_data(obj, "admin_users", RoleUserSerializer)

    def get_groups(self, obj):
        return self.get_filtered_data(obj, "groups", RoleGroupSerializer)

    def get_admin_groups(self, obj):
        return self.get_filtered_data(obj, "admin_groups", RoleGroupSerializer)

    def get_is_editable(self, obj: Role) -> bool:
        current_user: User = self.context["request"].user
        return Role.editable(current_user, obj.admin_users.all(), obj.admin_groups.all())


class RoleCreateUpdateSerializer(serializers.ModelSerializer):
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

    def validate(self, role: OrderedDict):
        if not role.get("admin_users") and not role.get("admin_groups"):
            raise RequiredParameterError("admin_users or admin_groups field is required")

        users: list[User] = role.get("users", [])
        groups: list[Group] = role.get("groups", [])
        admin_users: list[User] = role.get("admin_users", [])
        admin_groups: list[Group] = role.get("admin_groups", [])

        user: User = self.context["request"].user
        if not Role.editable(user, admin_users, admin_groups):
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


class RoleImportExportChildSerializer(serializers.ModelSerializer):
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

    def to_representation(self, instance: Role):
        def _get_permission_data(permission_obj):
            return {
                "obj_id": permission_obj.get_objid(),
                "permission": permission_obj.name,
            }

        return {
            "id": instance.id,
            "name": instance.name,
            "description": instance.description,
            "users": [x.username for x in instance.users.all()],
            "groups": [x.name for x in instance.groups.all()],
            "admin_users": [x.username for x in instance.admin_users.all()],
            "admin_groups": [x.name for x in instance.admin_groups.all()],
            "permissions": [_get_permission_data(x) for x in instance.permissions.all()],
        }


class RoleImportSerializer(serializers.ListSerializer):
    child = RoleImportExportChildSerializer()
