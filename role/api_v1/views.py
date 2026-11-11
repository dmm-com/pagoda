from typing import cast

from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from job.models import Job, JobOperation
from role.models import Role
from user.models import User


class RoleAPI(APIView):
    @extend_schema(
        responses={
            204: OpenApiTypes.STR,
            401: OpenApiTypes.STR,
            404: OpenApiTypes.STR,
        },
    )
    def delete(self, request: Request, role_id: int, format: str | None = None) -> Response:
        try:
            role = Role.objects.get(pk=role_id)
        except Role.DoesNotExist:
            return Response("Role not found(id:%s)" % role_id, status=status.HTTP_404_NOT_FOUND)

        user = cast(User, request.user)
        if user.is_readonly or not role.is_editable(user):
            return Response(
                "Permission error to delete the Role(%s)" % role.name,
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # This deletes target Role instance.
        # Just before doing it, this copies name for response message.
        role_name = role.name
        job = Job.new_role_change(
            user,
            role.pk,
            JobOperation.DELETE_ROLE,
            {},
            text=f"DELETE_ROLE: {role.name} (role #{role.pk})",
        )
        transaction.on_commit(job.run)
        return Response(
            "Succeeded in deleting Role(%s)" % role_name,
            status=status.HTTP_204_NO_CONTENT,
        )
