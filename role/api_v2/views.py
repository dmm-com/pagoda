from typing import Any, cast

from django.db import transaction
from django.db.models import Prefetch, Q, QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, generics, serializers, status, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from airone.lib.configuration_export import ConfigurationExportAPI
from airone.lib.drf import EnvelopeYAMLParser, IsSuperuser
from group.models import Group
from job.models import Job, JobOperation, JobStatus
from role.api_v2.serializers import (
    RoleCreateUpdateSerializer,
    RoleHistoryListSerializer,
    RoleHistorySerializer,
    RoleImportSerializer,
    RoleJobSerializer,
    RoleRestoreSerializer,
    RoleSerializer,
)
from role.history import role_history_events
from role.models import Role
from role.services import restore_data, validate_role_data
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
        if current_user.is_readonly and view.action in [
            "update",
            "partial_update",
            "destroy",
            "restore",
        ]:
            return False

        is_editable = Role.editable(
            current_user, list(obj.admin_users.all()), list(obj.admin_groups.all())
        )
        permission = {
            "retrieve": is_editable,
            "create": True,
            "destroy": is_editable,
            "update": is_editable,
            "partial_update": is_editable,
            "histories": is_editable,
            "restore": is_editable,
        }
        return permission.get(view.action, False)


class RoleAPI(viewsets.ModelViewSet[Role]):
    queryset = Role.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated & RolePermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self) -> QuerySet[Role]:
        base_queryset = Role.objects.all()
        if self.action not in ("histories", "restore"):
            base_queryset = base_queryset.filter(is_active=True)
        base_queryset = base_queryset.prefetch_related(
            Prefetch("users", queryset=User.objects.filter(is_active=True)),
            Prefetch("groups", queryset=Group.objects.filter(is_active=True)),
            Prefetch("admin_users", queryset=User.objects.filter(is_active=True)),
            Prefetch("admin_groups", queryset=Group.objects.filter(is_active=True)),
        )
        if self.action in ("retrieve", "histories", "restore"):
            return base_queryset
        return get_permitted_roles(cast(User, self.request.user), base_queryset)

    def get_serializer_class(self) -> type[serializers.Serializer[Any]]:
        serializer: dict[str, type[serializers.Serializer[Any]]] = {
            "create": RoleCreateUpdateSerializer,
            "update": RoleCreateUpdateSerializer,
            "histories": RoleHistorySerializer,
            "restore": RoleRestoreSerializer,
        }
        return serializer.get(self.action, RoleSerializer)

    @extend_schema(responses={202: RoleJobSerializer})
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        role = self.get_object()
        serializer = self.get_serializer(role, data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.enqueue_change(role, JobOperation.EDIT_ROLE, {"data": dict(request.data)})

    @extend_schema(responses={202: RoleJobSerializer})
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.enqueue_change(self.get_object(), JobOperation.DELETE_ROLE, {})

    def enqueue_change(
        self, role: Role, operation: JobOperation, params: dict[str, Any]
    ) -> Response:
        job = Job.new_role_change(
            cast(User, self.request.user),
            role.pk,
            operation,
            params,
            text=f"{operation.name}: {role.name} (role #{role.pk})",
        )
        transaction.on_commit(job.run)
        return Response({"job_id": job.pk}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(responses=RoleHistoryListSerializer)
    def histories(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        role = self.get_object()
        histories = role_history_events(role)
        pagination = LimitOffsetPagination()
        pagination.default_limit = 10
        pagination.max_limit = 100
        page: list[dict[str, Any]] | None = pagination.paginate_queryset(
            cast(Any, histories), request, view=self
        )
        serializer = RoleHistorySerializer(page if page is not None else histories, many=True)
        response = pagination.get_paginated_response(serializer.data)
        response.data["role"] = {
            "id": role.pk,
            "name": role.name,
            "is_active": role.is_active,
            "is_editable": role.is_editable(cast(User, request.user)),
        }
        return response

    @extend_schema(request=RoleRestoreSerializer, responses={202: RoleJobSerializer})
    def restore(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        role = self.get_object()
        serializer = RoleRestoreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        history_id = serializer.validated_data["history_id"]
        history_source = serializer.validated_data["history_source"]
        data, _ = restore_data(role, history_id, cast(User, request.user), history_source)
        validate_role_data(role, data, cast(User, request.user))
        return self.enqueue_change(
            role,
            JobOperation.RESTORE_ROLE,
            {"history_id": history_id, "history_source": history_source},
        )


class RoleImportAPI(generics.GenericAPIView[Any]):
    parser_classes = [EnvelopeYAMLParser]
    serializer_class = RoleImportSerializer
    # An imported role can take over any role and grant any permission on any object
    permission_classes = [IsAuthenticated & IsSuperuser]

    def post(self, request: Request) -> Response:
        import_datas = request.data
        user = cast(User, request.user)
        serializer = RoleImportSerializer(data=import_datas)
        serializer.is_valid(raise_exception=True)

        job = Job.new_role_import_v2(
            user, text="Preparing to import role data", params=serializer.validated_data
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

        return Response([], status=status.HTTP_200_OK)


@extend_schema_view(post=extend_schema(operation_id="role_api_v2_export_create"))
class RoleExportAPI(ConfigurationExportAPI):
    export_kind = "role"
