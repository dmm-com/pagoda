from collections import OrderedDict
from typing import List

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
    users = RoleUserSerializer(many=True)
    groups = RoleGroupSerializer(many=True)
    admin_users = RoleUserSerializer(many=True)
    admin_groups = RoleGroupSerializer(many=True)

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
        ]


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

        users: List[User] = role.get("users", [])
        groups: List[Group] = role.get("groups", [])
        admin_users: List[User] = role.get("admin_users", [])
        admin_groups: List[Group] = role.get("admin_groups", [])

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
    users = serializers.ListField(child=serializers.CharField())
    groups = serializers.ListField(child=serializers.CharField())
    admin_users = serializers.ListField(child=serializers.CharField())
    admin_groups = serializers.ListField(child=serializers.CharField())
    permissoins = serializers.ListField(child=serializers.DictField())

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
