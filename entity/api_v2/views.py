from distutils.util import strtobool

from django.db.models import F
from django.http import Http404
from django.http.response import HttpResponse, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

import custom_view
from airone.lib.acl import ACLType
from airone.lib.drf import ObjectNotExistsError
from airone.lib.http import http_get
from entity.api_v2.serializers import (
    EntityCreateSerializer,
    EntityDetailSerializer,
    EntityHistorySerializer,
    EntityListSerializer,
    EntityUpdateSerializer,
)
from entity.models import Entity, EntityAttr
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
            "list": ACLType.Readable,
            "create": ACLType.Writable,
        }

        entity = Entity.objects.filter(id=view.kwargs.get("entity_id"), is_active=True).first()

        if entity and not request.user.has_permission(entity, permisson.get(view.action)):
            return False

        view.entity = entity
        return True

    def has_object_permission(self, request, view, obj):
        user: User = request.user
        permisson = {
            "retrieve": ACLType.Readable,
            "update": ACLType.Writable,
            "destroy": ACLType.Full,
        }

        if not user.has_permission(obj, permisson.get(view.action)):
            return False

        return True


@extend_schema(
    parameters=[
        OpenApiParameter("is_toplevel", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
    ],
)
class EntityAPI(viewsets.ModelViewSet):
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticated & EntityPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["name"]
    ordering = ["name"]

    def get_serializer_class(self):
        serializer = {
            "list": EntityListSerializer,
            "create": EntityCreateSerializer,
            "update": EntityUpdateSerializer,
        }
        return serializer.get(self.action, EntityDetailSerializer)

    def get_queryset(self):
        is_toplevel = self.request.query_params.get("is_toplevel", None)

        filter_condition = {"is_active": True}
        exclude_condition = {}

        if is_toplevel is not None:
            if strtobool(is_toplevel):
                filter_condition["status"] = F("status").bitor(Entity.STATUS_TOP_LEVEL)
            else:
                exclude_condition["status"] = F("status").bitor(Entity.STATUS_TOP_LEVEL)

        return Entity.objects.filter(**filter_condition).exclude(**exclude_condition)

    def destroy(self, request, pk):
        entity: Entity = self.get_object()
        user: User = request.user

        if not entity.is_active:
            raise ObjectNotExistsError("specified entity has already been deleted")

        if Entry.objects.filter(schema=entity, is_active=True).exists():
            raise ValidationError(
                "cannot delete Entity because one or more Entries are not deleted"
            )

        if custom_view.is_custom("before_delete_entity_v2"):
            custom_view.call_custom("before_delete_entity_v2", None, user, entity)

        # register operation History for deleting entity
        history: History = user.seth_entity_del(entity)

        entity.delete()

        # Delete all attributes which target Entity have
        entity_attr: EntityAttr
        for entity_attr in entity.attrs.filter(is_active=True):
            history.del_attr(entity_attr)
            entity_attr.delete()

        if custom_view.is_custom("after_delete_entity_v2"):
            custom_view.call_custom("after_delete_entity_v2", None, user, entity)

        return Response(status=status.HTTP_204_NO_CONTENT)


class EntityEntryAPI(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated & EntityPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["is_active"]
    ordering_fields = ["name"]
    search_fields = ["name"]

    def get_serializer_class(self):
        serializer = {
            "create": EntryCreateSerializer,
        }
        return serializer.get(self.action, EntryBaseSerializer)

    def get_queryset(self):
        entity = Entity.objects.filter(id=self.kwargs.get("entity_id"), is_active=True).first()
        if not entity:
            raise Http404
        return self.queryset.filter(schema=entity)

    def create(self, request, entity_id):
        request.data["schema"] = entity_id
        return super().create(request)


class EntityHistoryAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = EntityHistorySerializer
    permission_classes = [IsAuthenticated & EntityPermission]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        entity = Entity.objects.get(id=self.kwargs.get("entity_id"))
        if not entity:
            raise Http404
        attrs = entity.attrs.all()

        entity_histories = History.objects.filter(target_obj=entity, is_detail=False)
        entity_attr_histories = History.objects.filter(target_obj__in=attrs, is_detail=True)

        return entity_histories.union(entity_attr_histories).order_by("-time")
