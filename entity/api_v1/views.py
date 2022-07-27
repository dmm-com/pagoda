from django.http.response import JsonResponse

from airone.lib.acl import ACLType
from airone.lib.http import http_get
from entity.models import Entity


@http_get
def get_entities(request):
    return JsonResponse(
        {
            "entities": [
                {
                    "id": x.id,
                    "name": x.name,
                    "status": x.status,
                    "note": x.note,
                }
                for x in Entity.objects.filter(is_active=True)
                if request.user.has_permission(x, ACLType.Readable)
            ]
        }
    )
