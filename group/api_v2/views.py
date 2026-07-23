from typing import Any, cast

from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, serializers, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from airone.lib.drf import YAMLParser, YAMLRenderer
from group.api_v2.serializers import (
    GroupCreateUpdateSerializer,
    GroupExportSerializer,
    GroupImportSerializer,
    GroupSerializer,
    GroupTreeSerializer,
)
from group.models import Group
from user.models import User


class UserPermission(BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: User) -> bool:
        current_user = cast(User, request.user)
        permisson = {
            "retrieve": True,
            "destroy": current_user.is_superuser,
            "create": current_user.is_superuser,
            "update": current_user.is_superuser,
        }
        return permisson.get(getattr(view, "action", ""), False)


class GroupAPI(viewsets.ModelViewSet[Group]):
    queryset = Group.objects.filter(is_active=True).prefetch_related(  # type: ignore[assignment,misc]
        Prefetch(
            "user_set",
            queryset=User.objects.filter(is_active=True).order_by("username"),
            to_attr="active_members",
        )
    )
    permission_classes = [IsAuthenticated & UserPermission]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
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
    queryset = Group.objects.filter(parent_group__isnull=True, is_active=True)  # type: ignore[assignment,misc]
    serializer_class = GroupTreeSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering = ["name"]
    search_fields = ["name"]


class GroupImportAPI(generics.GenericAPIView[Any]):
    parser_classes = [YAMLParser]
    serializer_class = GroupImportSerializer

    @extend_schema(responses={200: None})
    def post(self, request: Request) -> Response:
        import_datas: list[dict[str, Any]] = cast(list[dict[str, Any]], request.data)
        serializer = GroupImportSerializer(data=import_datas, many=True)
        serializer.is_valid(raise_exception=True)

        # TODO better to move the saving logic into the serializer
        for group_data in import_datas:
            if "id" in group_data:
                # update group by id
                group: Group | None = cast(
                    Group | None, Group.objects.filter(id=group_data["id"]).first()
                )
                if not group:
                    return Response(
                        "Specified id group does not exist(id:%s, group:%s)"
                        % (group_data["id"], group_data["name"]),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # check new name is not used
                if (group.name != group_data["name"]) and (
                    Group.objects.filter(name=group_data["name"]).count() > 0
                ):
                    return Response(
                        "New group name is already used(id:%s, group:%s->%s)"
                        % (group_data["id"], group.name, group_data["name"]),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                group.name = group_data["name"]
                group.save()
            else:
                # update group by name
                group = cast(Group | None, Group.objects.filter(name=group_data["name"]).first())
                if not group:
                    # create group
                    group = Group(name=group_data["name"])
                group.save()

        return Response(status=status.HTTP_200_OK)


class GroupExportAPI(generics.ListAPIView[Group]):
    queryset = Group.objects.filter(is_active=True)  # type: ignore[assignment,misc]
    serializer_class = GroupExportSerializer
    renderer_classes = [YAMLRenderer]
