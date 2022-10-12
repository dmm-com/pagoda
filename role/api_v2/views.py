from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from role.api_v2.serializers import RoleCreateUpdateSerializer, RoleSerializer
from role.models import Role


class RoleAPI(viewsets.ModelViewSet):
    queryset = Role.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        serializer = {
            "create": RoleCreateUpdateSerializer,
            "update": RoleCreateUpdateSerializer,
        }
        return serializer.get(self.action, RoleSerializer)
