from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from role.models import Role


class RoleAPI(APIView):
    def delete(self, request, role_id, format=None):
        try:
            role = Role.objects.get(pk=role_id)
        except Role.DoesNotExist:
            return Response("Role not found(id:%s)" % role_id,
                            status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if not role.permit_to_edit(user):
            return Response("Permission error to delete the Role(%s)" % role.name,
                            status=status.HTTP_401_UNAUTHORIZED)

        # This deletes target Role instance.
        # Just before doing it, this copies name for response message.
        role_name = role.name
        role.delete()
        return Response("Succeeded in deleting Role(%s)" % role_name,
                        status=status.HTTP_204_NO_CONTENT)
