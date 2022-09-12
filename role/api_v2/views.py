from rest_framework import viewsets

from role.api_v2.serializers import RoleSerializer
from role.models import Role


class RoleAPI(viewsets.ReadOnlyModelViewSet):
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleSerializer
