from airone.lib.acl import ACLType
from airone.lib.http import get_object_with_check_permission
from airone.lib.http import http_get
from airone.lib.http import render

from entity.models import Entity
from user.models import User


@http_get
def list_webhook(request, entity_id):
    user = User.objects.get(id=request.user.id)
    entity, error = get_object_with_check_permission(user, Entity, entity_id, ACLType.Full)
    if error:
        return error

    return render(
        request,
        "list_webhooks.html",
        {
            "entity": entity,
            "webhooks": entity.webhooks.all(),
        },
    )
