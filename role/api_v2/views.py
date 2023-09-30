from rest_framework import generics, serializers, status, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from acl.models import ACLBase
from airone.lib.drf import YAMLParser, YAMLRenderer
from group.models import Group
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
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer

    def post(self, request):
        import_datas = request.data
        serializer = RoleImportSerializer(data=import_datas)
        serializer.is_valid(raise_exception=True)

        # TODO better to move the saving logic into the serializer
        for role_data in import_datas:
            if "name" not in role_data:
                return Response("Role name is required", status=status.HTTP_400_BAD_REQUEST)

            if "id" in role_data:
                # update group by id
                role = Role.objects.filter(id=role_data["id"]).first()
                if not role:
                    return Response(
                        "Specified id role does not exist(id:%s, group:%s)"
                        % (role_data["id"], role_data["name"]),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # check new name is not used
                if (role.name != role_data["name"]) and (
                    Role.objects.filter(name=role_data["name"]).count() > 0
                ):
                    return Response(
                        "New role name is already used(id:%s, group:%s->%s)"
                        % (role_data["id"], role.name, role_data["name"]),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                role.name = role_data["name"]
            else:
                # update group by name
                role = Role.objects.filter(name=role_data["name"]).first()
                if not role:
                    # create group
                    role = Role.objects.create(name=role_data["name"])
                else:
                    # clear registered members (users, groups and administrative ones) to that role
                    for key in ["users", "groups", "admin_users", "admin_groups"]:
                        getattr(role, key).clear()

            role.description = role_data["description"]

            # set registered members (users, groups and administrative ones) to that role
            for key in ["users", "admin_users"]:
                for name in role_data[key]:
                    instance = User.objects.filter(username=name, is_active=True).first()
                    if not instance:
                        return Response(
                            "specified user is not found (username: %s)" % name,
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    getattr(role, key).add(instance)
            for key in ["groups", "admin_groups"]:
                for name in role_data[key]:
                    instance = Group.objects.filter(name=name, is_active=True).first()
                    if not instance:
                        return Response(
                            "specified group is not found (name: %s)" % name,
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    getattr(role, key).add(instance)

            for permission in role_data.get("permissions", []):
                acl = ACLBase.objects.filter(id=permission["obj_id"]).first()
                if not acl:
                    return Response(
                        "Invalid obj_id given: %s" % str(permission["obj_id"]),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if permission["permission"] == "readable":
                    acl.readable.roles.add(role)
                elif permission["permission"] == "writable":
                    acl.writable.roles.add(role)
                elif permission["permission"] == "full":
                    acl.full.roles.add(role)

            role.save()

        return Response()


class RoleExportAPI(generics.ListAPIView):
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleImportExportChildSerializer
    renderer_classes = [YAMLRenderer]
    permission_classes = [IsAuthenticated]
