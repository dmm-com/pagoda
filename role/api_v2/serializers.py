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

        user: User = self.context["request"].user
        if not Role.editable(user, role.get("admin_users", []), role.get("admin_groups", [])):
            raise RequiredParameterError(
                "your account must be set as a member of admin_users or admin_groups"
            )

        return role
