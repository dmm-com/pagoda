import itertools

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from acl.api_v2.serializers import ACLHistorySerializer, ACLSerializer
from acl.models import ACLBase
from airone.lib.acl import ACLType
from role.models import HistoricalPermission


class ACLFullPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, ACLBase):
            return False
        if not request.user.has_permission(obj, ACLType.Full):
            return False
        return True


class ACLAPI(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = ACLBase.objects.all()
    serializer_class = ACLSerializer

    permission_classes = [IsAuthenticated & ACLFullPermission]


@extend_schema(
    parameters=[
        OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH),
    ]
)
class ACLHistoryAPI(generics.ListAPIView):
    serializer_class = ACLHistorySerializer

    def get_queryset(self):
        """Unnecessary in this serializer"""
        pass

    def get(self, request, pk: int):
        acl = ACLBase.objects.filter(id=pk).first()
        acl_history = list(acl.get_subclass_object().history.all())

        permissions = HistoricalPermission.objects.filter(codename__startswith="%s." % pk)
        permission_history = list(
            itertools.chain.from_iterable([p.history.all() for p in permissions])
        )

        serializer = ACLHistorySerializer(data=acl_history + permission_history, many=True)
        serializer.is_valid()

        # filter histories have empty changes
        # then, order by time desc
        transformed = sorted(
            [h for h in serializer.data if h["changes"]], reverse=True, key=lambda x: x["time"]
        )

        return Response(transformed)
