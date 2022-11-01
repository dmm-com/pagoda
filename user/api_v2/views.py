import io
from typing import List, TypedDict

import yaml
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from airone.lib.drf import YAMLParser
from group.models import Group
from user.api_v2.serializers import (
    UserCreateSerializer,
    UserImportSerializer,
    UserListSerializer,
    UserRetrieveSerializer,
    UserTokenSerializer,
    UserUpdateSerializer,
)
from user.models import User


class UserExport(TypedDict):
    id: int
    username: str
    email: str
    groups: str


class UserPermission(BasePermission):
    def has_object_permission(self, request, view, obj: User):
        current_user: User = request.user
        permisson = {
            "retrieve": current_user.is_superuser or current_user == obj,
            "destroy": current_user.is_superuser,
            "update": current_user.is_superuser or current_user == obj,
        }
        return permisson.get(view.action)


class UserAPI(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated & UserPermission]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering = ["username"]
    search_fields = ["username"]

    def get_serializer_class(self):
        serializer = {
            "create": UserCreateSerializer,
            "update": UserUpdateSerializer,
            "list": UserListSerializer,
        }
        return serializer.get(self.action, UserRetrieveSerializer)

    def destroy(self, request, pk):
        user: User = self.get_object()
        user.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserTokenAPI(viewsets.ModelViewSet):
    serializer_class = UserTokenSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request):
        instance = get_object_or_404(Token.objects.filter(user=request.user))
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def refresh(self, request):
        Token.objects.filter(user=request.user).delete()
        instance = Token.objects.create(user=request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UserImportAPI(generics.GenericAPIView):
    parser_classes = [YAMLParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import_datas = request.data
        serializer = UserImportSerializer(data=import_datas)
        serializer.is_valid(raise_exception=True)

        # TODO better to move the saving logic into the serializer
        for user_data in import_datas:
            for param in ["username", "groups", "email"]:
                if param not in user_data:
                    return Response("'%s' is required" % param, status=400)

            user = None
            if "id" in user_data:
                # update user by id when id is specified
                user = User.objects.filter(id=user_data["id"]).first()
                if not user:
                    return Response(
                        "Specified id user does not exist(id:%s, user:%s)"
                        % (user_data["id"], user_data["username"]),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if (user.username != user_data["username"]) and (
                    User.objects.filter(username=user_data["username"]).count() > 0
                ):
                    return Response(
                        "New username is already used(id:%s, user:%s->%s)"
                        % (user_data["id"], user.username, user_data["username"]),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                # update user by username
                user = User.objects.filter(username=user_data["username"]).first()
                if not user:
                    # create user
                    user = User(username=user_data["username"])
                    user.save()

            user.username = user_data["username"]
            user.email = user_data["email"]

            new_groups = []
            for group_name in user_data["groups"].split(","):
                if group_name == "":
                    continue
                new_group = Group.objects.filter(name=group_name).first()
                if not new_group:
                    return Response(
                        "Specified group does not exist(user:%s, group:%s)"
                        % (user_data["username"], group_name),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                new_groups.append(new_group)

            user.groups.set(new_groups)
            user.save()

        return Response()


class UserExportAPI(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        data: List[UserExport] = []

        for user in User.objects.filter(is_active=True):
            data.append(
                {
                    "email": user.email,
                    "groups": ",".join(
                        list(map(lambda x: x.name, user.groups.filter(group__is_active=True)))
                    ),
                    "id": user.id,
                    "username": user.username,
                }
            )

        output = io.StringIO()
        output.write(yaml.dump(data, default_flow_style=False, allow_unicode=True))

        return HttpResponse(output.getvalue(), content_type="application/yaml")
