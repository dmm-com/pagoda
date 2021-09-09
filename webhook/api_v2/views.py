from api_v1.auth import AironeTokenAuth

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from airone.lib.profile import airone_profile
from entity.models import Entity


class WebhookAPI(APIView):
    authentication_classes = (AironeTokenAuth, BasicAuthentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    @airone_profile
    def get(self, request, entity_id):
        entity = Entity.objects.filter(id=entity_id, is_active=True).first()
        if entity is None:
            return Response({'msg': 'There is no entity for setting'},
                            content_type='application/json; charset=UTF-8', status=400)

        return Response([x.to_dict() for x in entity.webhooks.all()],
                        content_type='application/json; charset=UTF-8')
