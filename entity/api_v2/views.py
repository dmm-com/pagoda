from airone.lib.profile import airone_profile
from airone.lib.http import http_get

from entity.models import Entity

from django.http import HttpResponse
from django.http.response import JsonResponse

from user.models import History


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
