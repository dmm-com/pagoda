import json
import requests

from airone.lib.profile import airone_profile
from airone.lib.http import check_permission
from airone.lib.http import http_get, http_post
from airone.lib.acl import ACLType

from entity.models import Entity

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import HttpResponse
from django.http.response import JsonResponse
from user.models import User


@airone_profile
@http_get
def get_entities(request):
    user = User.objects.get(id=request.user.id)

    return JsonResponse({
        'entities': [{
            'id': x.id,
            'name': x.name,
        } for x in Entity.objects.filter(is_active=True)
            if user.has_permission(x, ACLType.Readable)]
    })


@airone_profile
@http_post([
    {'name': 'webhook_url', 'type': str},
    {'name': 'is_enabled_webhook', 'type': bool},
    {'name': 'request_headers', 'type': list},
])
@check_permission(Entity, ACLType.Full)
def settings(request, entity_id, recv_data):
    entity = Entity.objects.filter(id=entity_id, is_active=True).first()
    if not entity:
        return JsonResponse({'msg': 'There is no entity for setting'}, status=400)

    # check specified parameters are valid
    validate = URLValidator()
    try:
        # This checks webhook_url is valid HTTP URL
        validate(recv_data['webhook_url'])

    except ValidationError:
        return HttpResponse('Specified URL is invalid', status=400)

    # check specified webhook endpoint is valid
    request_headers = {x['key']: x['value'] for x in recv_data['request_headers']}

    resp = requests.post(recv_data['webhook_url'], **{
        'headers': request_headers,
        'data': json.dumps({}),
        'verify': False,
    })
    if not resp.ok:
        return HttpResponse("Failed send message to the endpoint: %s" % str(resp.text), status=400)

    # update notification's settings of Entity
    entity.webhook_url = recv_data['webhook_url']
    entity.webhook_headers = json.dumps(request_headers)
    entity.is_enabled_webhook = recv_data['is_enabled_webhook']
    entity.save(update_fields=['webhook_url', 'webhook_headers', 'is_enabled_webhook'])

    return HttpResponse('Succeded in making notification settings for entity')
