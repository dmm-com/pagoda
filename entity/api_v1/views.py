from airone.lib.http import http_get
from airone.lib.acl import ACLType

from entity.models import Entity

from django.http.response import JsonResponse
from user.models import User


@http_get
def get_entities(request):
    user = User.objects.get(id=request.user.id)

    return JsonResponse({
        'entities': [{
            'id': x.id,
            'name': x.name,
            'status': x.status,
            'note': x.note,
        } for x in Entity.objects.filter(is_active=True)
            if user.has_permission(x, ACLType.Readable)]
    })
