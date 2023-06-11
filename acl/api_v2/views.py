from rest_framework import mixins, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from acl.api_v2.serializers import ACLSerializer, ACLHistorySerializer
from acl.models import ACLBase
from airone.lib.acl import ACLType


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


class ACLHistoryAPI(viewsets.GenericViewSet):
    serializer_class = ACLHistorySerializer

    def get_queryset(self):
        pk: int = self.kwargs["pk"]
        acl = ACLBase.objects.filter(id=pk).first()

        acl_history = acl.get_subclass_object().history.all()

        # FIXME experiment to get both ACL level and permission level history
        # NOTE probably its hard to combine histories from different models
        # so we need to search a workaround, like having 2 serializers then generating 1 response
        # permission = HistoricalPermission.objects.filter(codename__startswith="%s." % pk)
        # print(acl_history.union(*[p.history.all() for p in permission], all=True))

        return acl_history

    def get(self, request, pk: int):
        queryset = self.get_queryset()

        serializer = ACLHistorySerializer(queryset, many=True)

        return Response(serializer.data)
