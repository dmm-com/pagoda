from rest_framework import filters, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.http import Http404
from django.http.response import JsonResponse, HttpResponse
from django_filters.rest_framework import DjangoFilterBackend

from airone.lib.acl import ACLType
from airone.lib.http import http_get
from entity.api_v2.serializers import EntityWithAttrSerializer
from entity.models import Entity
from entry.api_v2.serializers import EntryBaseSerializer, EntryCreateSerializer
from entry.models import Entry
from user.models import History, User


@http_get
def history(request, entity_id):
    if not Entity.objects.filter(id=entity_id).exists():
        return HttpResponse("Failed to get entity of specified id", status=400)

    # entity to be editted is given by url
    entity = Entity.objects.get(id=entity_id)
    histories = History.objects.filter(target_obj=entity, is_detail=False).order_by("-time")

    return JsonResponse(
        [
            {
                "user": {
                    "username": h.user.username,
                },
                "operation": h.operation,
                "details": [
                    {
                        "operation": d.operation,
                        "target_obj": {
                            "name": d.target_obj.name,
                        },
                        "text": d.text,
                    }
                    for d in h.details.all()
                ],
                "time": h.time,
            }
            for h in histories
        ],
        safe=False,
    )


class EntityPermission(BasePermission):
    def has_permission(self, request, view):
        permisson = {
            'list': ACLType.Readable,
            'create': ACLType.Writable,
        }

        user: User = User.objects.get(id=request.user.id)
        entity = Entity.objects.filter(id=view.kwargs.get('entity_id'), is_active=True).first()

        if entity and not user.has_permission(entity, permisson.get(view.action)):
            return False

        view.entity = entity
        return True


class EntityAPI(viewsets.ReadOnlyModelViewSet):
    queryset = Entity.objects.filter(is_active=True)
    serializer_class = EntityWithAttrSerializer


class EntityEntryAPI(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated & EntityPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['is_active']
    ordering_fields = ['name']
    search_fields = ['name']

    def get_serializer_class(self):
        serializer = {
            'create': EntryCreateSerializer,
        }
        return serializer.get(self.action, EntryBaseSerializer)

    def get_queryset(self):
        entity = Entity.objects.filter(id=self.kwargs.get('entity_id'), is_active=True).first()
        if not entity:
            raise Http404
        return self.queryset.filter(schema=entity)

    def create(self, request, entity_id):
        request.data['schema'] = entity_id
        return super().create(request)
