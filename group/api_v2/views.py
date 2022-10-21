from rest_framework import viewsets

from group.api_v2.serializers import GroupSerializer, GroupTreeSerializer
from group.models import Group


class GroupAPI(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.filter(is_active=True)
    serializer_class = GroupSerializer


class GroupTreeAPI(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.filter(parent_group__isnull=True, is_active=True)
    serializer_class = GroupTreeSerializer
