from typing import Any, Dict, List

from rest_framework import serializers

from group.models import Group
from user.models import User


class GroupSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField(method_name="get_members")

    class Meta:
        model = Group
        fields = ["id", "name", "members"]

    def get_members(self, obj: Group) -> List[Dict[str, Any]]:
        users = User.objects.filter(groups__name=obj.name, is_active=True).order_by("username")
        return [
            {
                "id": u.id,
                "username": u.username,
            }
            for u in users
        ]


class GroupTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField(method_name="get_children")

    class Meta:
        model = Group
        fields = ["id", "name", "children"]

    def get_children(self, obj: Group) -> List[Dict]:
        def _make_hierarchical_group(groups: List[Group]) -> List[Dict]:
            return [
                {
                    "id": g.id,
                    "name": g.name,
                    "children": _make_hierarchical_group(g.subordinates.filter(is_active=True)),
                }
                for g in groups
            ]

        return _make_hierarchical_group(obj.subordinates.filter(is_active=True))
