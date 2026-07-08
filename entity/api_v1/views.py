from typing import cast

from django.http import HttpRequest
from django.http.response import JsonResponse

from airone.lib.acl import ACLType
from airone.lib.http import http_get
from entity.models import Entity
from user.models import User


@http_get
def get_entities(request: HttpRequest) -> JsonResponse:
    # http_get already rejects unauthenticated requests, so request.user is a User.
    user = cast(User, request.user)
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
                if user.has_permission(x, ACLType.Readable)
            ]
        }
    )
