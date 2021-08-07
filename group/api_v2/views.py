from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets

from group.api_v2.serializers import GroupSerializer, GroupDetailSerializer
from group.models import Group


class GroupAPI(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.filter(is_active=True)
    serializer_class = GroupSerializer

    @extend_schema(responses={200: GroupDetailSerializer})
    @action(detail=True)
    def retrieve(self, request, pk=None):
        ser = GroupDetailSerializer(self.get_object())
        return Response(ser.data, status.HTTP_200_OK)
