from airone.lib.acl import ACLType
from airone.lib.http import get_obj_with_check_perm, http_get, render
from entity.models import Entity


@http_get
def list_webhook(request, entity_id):
    entity, error = get_obj_with_check_perm(request.user, Entity, entity_id, ACLType.Full)
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
