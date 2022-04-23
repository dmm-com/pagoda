from rest_framework import mixins, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated

from acl.api_v2.serializers import ACLSerializer
from acl.models import ACLBase
from airone.lib.acl import ACLType
from user.models import User


class ACLFullPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, ACLBase):
            return False
        user = User.objects.get(id=request.user.id)
        if not user.has_permission(obj, ACLType.Full):
            return False
        return True


class ACLAPI(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    queryset = ACLBase.objects.all()
    serializer_class = ACLSerializer

    permission_classes = [IsAuthenticated & ACLFullPermission]
