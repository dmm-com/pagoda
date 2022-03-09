from rest_framework import viewsets

from entity.api_v2.serializers import EntitySerializer
from user.models import History
from airone.lib.profile import airone_profile
from airone.lib.http import http_get

from django.http.response import JsonResponse, HttpResponse

from entity.models import Entity


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


class EntityAPI(viewsets.ReadOnlyModelViewSet):
    queryset = Entity.objects.filter(is_active=True)
    serializer_class = EntitySerializer
