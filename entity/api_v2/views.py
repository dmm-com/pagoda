from user.models import History
from airone.lib.acl import ACLType
from airone.lib.profile import airone_profile
from airone.lib.http import http_get

from django.http.response import JsonResponse, HttpResponse

from rest_framework.authtoken.models import Token

from entity.models import Entity
from user.models import User


@airone_profile
@http_get
def history(request, entity_id):
    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse('Failed to get entity of specified id', status=400)

    # entity to be editted is given by url
    entity = Entity.objects.get(id=entity_id)
    histories = History.objects.filter(target_obj=entity, is_detail=False).order_by('-time')

    return JsonResponse([{
        'user': {
            'username': h.user.username,
        },
        'operation': h.operation,
        'details': [{
            'operation': d.operation,
            'target_obj': {
                'name': d.target_obj.name,
            },
            'text': d.text,
        } for d in h.details.all()],
        'time': h.time,
    } for h in histories], safe=False)


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
