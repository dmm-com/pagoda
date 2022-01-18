from rest_framework.response import Response
from rest_framework.views import APIView

from airone.lib.profile import airone_profile
from entity.models import Entity


class WebhookAPI(APIView):

    @airone_profile
    def get(self, request, entity_id):
        entity = Entity.objects.filter(id=entity_id, is_active=True).first()
        if entity is None:
            return Response({'msg': 'There is no entity for setting'}, status=400)

        return Response([x.to_dict() for x in entity.webhooks.all()])
