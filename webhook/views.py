from typing import cast

from django.http import HttpRequest, HttpResponse

from airone.lib.acl import ACLType
from airone.lib.http import get_obj_with_check_perm, http_get, render
from entity.models import Entity
from user.models import User


@http_get
def list_webhook(request: HttpRequest, entity_id: int) -> HttpResponse:
    entity, error = get_obj_with_check_perm(
        cast(User, request.user),
        Entity,
        entity_id,
        ACLType.Full,
    )
    if error or not entity:
        assert error is not None
        return error

    return render(
        request,
        "list_webhooks.html",
        {
            "entity": entity,
            "webhooks": entity.webhooks.all(),
        },
    )
