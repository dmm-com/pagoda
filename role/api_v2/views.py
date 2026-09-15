from typing import Any, cast

from django.db.models import Prefetch, Q, QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, serializers, status, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from airone.lib.drf import YAMLParser, YAMLRenderer
from group.models import Group
from job.models import Job, JobStatus
from role.api_v2.serializers import (
    RoleCreateUpdateSerializer,
    RoleImportExportChildSerializer,
    RoleImportSerializer,
    RoleSerializer,
)
from role.models import Role
from user.models import User


def get_permitted_roles(user: User, base_queryset: QuerySet[Role]) -> QuerySet[Role]:
    """Return roles that the user is permitted to see."""
    if user.is_superuser:
        return base_queryset

    user_group_ids = [g.id for g in user.belonging_groups()]
    return base_queryset.filter(
        Q(users=user)
        | Q(admin_users=user)
        | Q(groups__id__in=user_group_ids)
        | Q(admin_groups__id__in=user_group_ids)
    ).distinct()


class RolePermission(BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:
        user = cast(User, request.user)
        if user.is_readonly and view.action == "create":
            return False
        return True

    def has_object_permission(self, request: Request, view: Any, obj: Role) -> bool:
        current_user = cast(User, request.user)
        if current_user.is_readonly and view.action in ["update", "destroy"]:
            return False

        is_editable = Role.editable(
            current_user, list(obj.admin_users.all()), list(obj.admin_groups.all())
        )
        permission = {
            "retrieve": True,
            "create": True,
            "destroy": is_editable,
            "update": is_editable,
        }
        return permission.get(view.action, False)


class RoleAPI(viewsets.ModelViewSet[Role]):
    queryset = Role.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated & RolePermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self) -> QuerySet[Role]:
        base_queryset = Role.objects.filter(is_active=True).prefetch_related(
            Prefetch("users", queryset=User.objects.filter(is_active=True)),
            Prefetch("groups", queryset=Group.objects.filter(is_active=True)),  # type: ignore[misc]
            Prefetch("admin_users", queryset=User.objects.filter(is_active=True)),
            Prefetch("admin_groups", queryset=Group.objects.filter(is_active=True)),  # type: ignore[misc]
        )
        return get_permitted_roles(cast(User, self.request.user), base_queryset)

    def get_serializer_class(self) -> type[serializers.Serializer[Any]]:
        serializer: dict[str, type[serializers.Serializer[Any]]] = {
            "create": RoleCreateUpdateSerializer,
            "update": RoleCreateUpdateSerializer,
        }
        return serializer.get(self.action, RoleSerializer)


class RoleImportAPI(generics.GenericAPIView[Any]):
    parser_classes = [YAMLParser]
    serializer_class = RoleImportSerializer

    def post(self, request: Request) -> Response:
        import_datas = request.data
        user = cast(User, request.user)
        serializer = RoleImportSerializer(data=import_datas)
        serializer.is_valid(raise_exception=True)

        job = Job.new_role_import_v2(
            user, text="Preparing to import role data", params=import_datas
        )
        try:
            task_result = job.run()
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(task_result, tuple) and task_result:
            task_status = task_result[0]
            if task_status in (JobStatus.ERROR, JobStatus.WARNING):
                return Response(
                    {"detail": task_result[1] if len(task_result) > 1 else "Role import failed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        # The generated TypeScript client expects the 200 response to be a
        # RoleImportExportChild array, as defined in OpenAPI.  The import is
        # asynchronous, so there is no completed role payload to return here.
        return Response([], status=status.HTTP_200_OK)


class RoleExportAPI(generics.ListAPIView[Role]):
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleImportExportChildSerializer
    renderer_classes = [YAMLRenderer]

    def get_queryset(self) -> QuerySet[Role]:
        return get_permitted_roles(
            cast(User, self.request.user), Role.objects.filter(is_active=True)
        )
