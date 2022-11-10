from rest_framework import viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated

from group.api_v2.serializers import (
    GroupCreateUpdateSerializer,
    GroupSerializer,
    GroupTreeSerializer,
)
from group.models import Group
from user.models import User


class UserPermission(BasePermission):
    def has_object_permission(self, request, view, obj: User):
        current_user: User = request.user
        permisson = {
            "retrieve": True,
            "destroy": current_user.is_superuser,
            "create": current_user.is_superuser,
            "update": current_user.is_superuser,
        }
        return permisson.get(view.action)


class GroupAPI(viewsets.ModelViewSet):
    queryset = Group.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated & UserPermission]

    def get_serializer_class(self):
        serializer = {
            "create": GroupCreateUpdateSerializer,
            "update": GroupCreateUpdateSerializer,
        }
        return serializer.get(self.action, GroupSerializer)


class GroupTreeAPI(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.filter(parent_group__isnull=True, is_active=True)
    serializer_class = GroupTreeSerializer
    permission_classes = [IsAuthenticated]
