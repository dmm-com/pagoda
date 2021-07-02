from airone.lib.acl import ACLType
from airone.lib.http import check_permission
from airone.lib.http import http_get
from airone.lib.http import render
from airone.lib.profile import airone_profile

from entity.models import Entity


@airone_profile
@http_get
@check_permission(Entity, ACLType.Full)
def list_webhook(request, entity_id):
    # entity of specifying id
    entity = Entity.objects.get(id=entity_id)

    return render(request, 'list_webhooks.html', {
        'entity': entity,
        'webhooks': entity.webhooks.all(),
    })
