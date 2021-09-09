import json
import requests
from airone.lib.acl import ACLType
from airone.lib.http import check_permission
from airone.lib.http import http_get
from airone.lib.profile import airone_profile
from django.http.response import JsonResponse


@airone_profile
@http_get
@check_permission(Entity, ACLType.Full)
def get_webhook(request, entity_id):
    entity = Entity.objects.filter(id=entity_id, is_active=True).first()
    if entity is None:
        return JsonResponse({'msg': 'There is no entity for setting'}, status=400)

    return JsonResponse({
        'label': 
        entity.webhook.all()
    })
