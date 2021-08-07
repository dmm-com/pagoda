from airone.lib.acl import ACLType
from airone.lib.profile import airone_profile
from airone.lib.http import http_get

from django.http.response import JsonResponse, HttpResponse

from rest_framework.authtoken.models import Token

from entity.models import Entity
from user.models import User


@airone_profile
@http_get
def get_entity(request, entity_id):
    user = User.objects.get(id=request.user.id)

    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse('Failed to get entity of specified id', status=400)

    # entity to be editted is given by url
    entity = Entity.objects.get(id=entity_id)

    (token, _) = Token.objects.get_or_create(user=user)
    return JsonResponse({
        'name': entity.name,
        'note': entity.note,
        'is_toplevel': (entity.status & Entity.STATUS_TOP_LEVEL) != 0,
        'attributes': [{
            'id': x.id,
            'name': x.name,
            'type': x.type,
            'is_mandatory': x.is_mandatory,
            'is_delete_in_chain': x.is_delete_in_chain,
            'referrals': [{
                'id': r.id,
                'name': r.name,
            } for r in x.referral.all()],
        } for x in entity.attrs.filter(is_active=True).order_by('index')
            if user.has_permission(x, ACLType.Writable)],
    })
