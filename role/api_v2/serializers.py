from rest_framework import serializers
from role.models import Role


class RoleSerializer(serializers.ModelSerializer):
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
