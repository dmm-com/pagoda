from rest_framework import viewsets

from group.api_v2.serializers import GroupSerializer
from group.models import Group


class GroupAPI(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.filter(is_active=True)
    serializer_class = GroupSerializer
