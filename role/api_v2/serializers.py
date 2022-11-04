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
