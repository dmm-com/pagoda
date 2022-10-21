from rest_framework import viewsets

from group.api_v2.serializers import (
    GroupCreateUpdateSerializer,
    GroupSerializer,
    GroupTreeSerializer,
)
from group.models import Group


class GroupAPI(viewsets.ModelViewSet):
    queryset = Group.objects.filter(is_active=True)

    def get_serializer_class(self):
        serializer = {
            "create": GroupCreateUpdateSerializer,
            "update": GroupCreateUpdateSerializer,
        }
        return serializer.get(self.action, GroupSerializer)


class GroupTreeAPI(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.filter(parent_group__isnull=True, is_active=True)
    serializer_class = GroupTreeSerializer
