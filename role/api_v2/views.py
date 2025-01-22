from rest_framework import generics, serializers, status, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from airone.lib.drf import YAMLParser, YAMLRenderer
from job.models import Job
from role.api_v2.serializers import (
    RoleCreateUpdateSerializer,
    RoleImportExportChildSerializer,
    RoleImportSerializer,
    RoleSerializer,
)
from role.models import Role
from user.models import User


class RolePermission(BasePermission):
    def has_object_permission(self, request, view, obj: Role):
        current_user: User = request.user
        is_editable = Role.editable(current_user, obj.admin_users.all(), obj.admin_groups.all())
        permission = {
            "retrieve": True,
            "create": True,
            "destroy": is_editable,
            "update": is_editable,
        }
        return permission.get(view.action)


class RoleAPI(viewsets.ModelViewSet):
    queryset = Role.objects.filter(is_active=True).prefetch_related("admin_users", "admin_groups")
    permission_classes = [IsAuthenticated & RolePermission]

    def get_serializer_class(self):
        serializer = {
            "create": RoleCreateUpdateSerializer,
            "update": RoleCreateUpdateSerializer,
        }
        return serializer.get(self.action, RoleSerializer)


class RoleImportAPI(generics.GenericAPIView):
    parser_classes = [YAMLParser]
    serializer_class = serializers.Serializer

    def post(self, request):
        import_datas = request.data
        user: User = request.user
        serializer = RoleImportSerializer(data=import_datas)
        serializer.is_valid(raise_exception=True)

        job_ids = []
        error_list = []

        job = Job.new_role_import_v2(
            user, text="Preparing to import role data", params=import_datas
        )
        job.run()
        job_ids.append(job.id)
        return Response(
            {"result": {"job_ids": job_ids, "error": error_list}}, status=status.HTTP_200_OK
        )


class RoleExportAPI(generics.ListAPIView):
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleImportExportChildSerializer
    renderer_classes = [YAMLRenderer]
    permission_classes = [IsAuthenticated]
