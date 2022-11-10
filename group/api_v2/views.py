import io
from typing import List, TypedDict

import yaml
from django.http import HttpResponse
from rest_framework import generics, status, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from airone.lib.drf import YAMLParser
from group.api_v2.serializers import (
    GroupCreateUpdateSerializer,
    GroupImportSerializer,
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


class GroupExport(TypedDict):
    id: int
    name: str


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


class GroupImportAPI(generics.GenericAPIView):
    parser_classes = [YAMLParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import_datas = request.data
        serializer = GroupImportSerializer(data=import_datas)
        serializer.is_valid(raise_exception=True)

        # TODO better to move the saving logic into the serializer
        for group_data in import_datas:
            if "name" not in group_data:
                return Response("Group name is required", status=status.HTTP_400_BAD_REQUEST)

            if "id" in group_data:
                # update group by id
                group = Group.objects.filter(id=group_data["id"]).first()
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
                group = Group.objects.filter(name=group_data["name"]).first()
                if not group:
                    # create group
                    group = Group(name=group_data["name"])
                group.save()

        return Response(status=status.HTTP_200_OK)


class GroupExportAPI(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        data: List[GroupExport] = []

        for group in Group.objects.filter(is_active=True):
            data.append(
                {
                    "id": group.id,
                    "name": group.name,
                }
            )

        output = io.StringIO()
        output.write(yaml.dump(data, default_flow_style=False, allow_unicode=True))

        return HttpResponse(output.getvalue(), content_type="application/yaml")
