from api_v1.auth import AironeTokenAuth

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from user.models import User
from entry.models import Entry


class EntryAPI(APIView):
    authentication_classes = (AironeTokenAuth, BasicAuthentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, entry_id, *args, **kwargs):
        print('[onix-test/EntryAPI.get(00)] entry_id: %s' % str(entry_id))

        user = User.objects.filter(id=request.user.id).first()

        # make a query based on GET parameters
        entry = Entry.objects.filter(id=entry_id, is_active=True).first()
        if not entry:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        return Response(entry.to_dict(user))
