from airone.lib.profile import airone_profile
from airone.lib.http import http_get
from airone.lib.acl import ACLType

from entity.models import Entity
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
