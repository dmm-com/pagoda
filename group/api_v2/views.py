import unicodedata
from typing import Any, cast

from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, generics, serializers, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from airone.exceptions import ImportDataError
from airone.lib.configuration_export import ConfigurationExportAPI
from airone.lib.drf import IsSuperuser, YAMLParser
from group.api_v2.serializers import (
    GroupCreateUpdateSerializer,
    GroupImportSerializer,
    GroupSerializer,
    GroupTreeV2Serializer,
)
from group.import_service import import_groups
from group.models import Group
from user.models import User


class UserPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        # create has no object, so has_object_permission() never runs for it
        if getattr(view, "action", "") == "create":
            return cast(User, request.user).is_superuser
        return True

    def has_object_permission(self, request: Request, view: APIView, obj: User) -> bool:
        current_user = cast(User, request.user)
        permisson = {
            "retrieve": True,
            "destroy": current_user.is_superuser,
            "create": current_user.is_superuser,
            "update": current_user.is_superuser,
        }
        return permisson.get(getattr(view, "action", ""), False)


class GroupSearchFilter(filters.SearchFilter):
    def filter_queryset(self, request: Request, queryset: Any, view: APIView) -> Any:
        terms = self.get_search_terms(request)
        if not terms:
            return queryset

        normalized_terms = [unicodedata.normalize("NFKC", term).casefold() for term in terms]
        return [
            group
            for group in queryset
            if all(
                term in unicodedata.normalize("NFKC", group.name).casefold()
                for term in normalized_terms
            )
        ]


class GroupAPI(viewsets.ModelViewSet[Group]):
    queryset = Group.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            "user_set",
            queryset=User.objects.filter(is_active=True).order_by("username"),
            to_attr="active_members",
        )
    )
    permission_classes = [IsAuthenticated & UserPermission]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, GroupSearchFilter]
    ordering = ["name"]
    search_fields = ["name"]

    def get_serializer_class(self) -> type[serializers.Serializer[Any]]:
        serializer: dict[str, type[serializers.Serializer[Any]]] = {
            "create": GroupCreateUpdateSerializer,
            "update": GroupCreateUpdateSerializer,
            "destroy": serializers.Serializer,
        }
        return serializer.get(self.action, GroupSerializer)


class GroupTreeAPI(viewsets.ReadOnlyModelViewSet[Group]):
    queryset = Group.objects.filter(parent_group__isnull=True, is_active=True)
    serializer_class = GroupTreeV2Serializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, GroupSearchFilter]
    ordering = ["name"]
    search_fields = ["name"]


class GroupImportAPI(generics.GenericAPIView[Any]):
    parser_classes = [YAMLParser]
    serializer_class = GroupImportSerializer
    permission_classes = [IsAuthenticated & IsSuperuser]

    @extend_schema(responses={200: None})
    def post(self, request: Request) -> Response:
        import_datas: list[dict[str, Any]] = cast(list[dict[str, Any]], request.data)
        serializer = GroupImportSerializer(data=import_datas, many=True)
        serializer.is_valid(raise_exception=True)

        try:
            import_groups(import_datas)
        except ImportDataError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


@extend_schema_view(get=extend_schema(operation_id="group_api_v2_groups_export_list"))
class GroupExportAPI(ConfigurationExportAPI):
    export_kind = "group"
