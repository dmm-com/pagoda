from distutils.util import strtobool

from django.db.models import Count, F
from django.http import Http404
from django.http.response import HttpResponse, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, generics, serializers, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer

import custom_view
from airone.lib.acl import ACLType, get_permitted_objects
from airone.lib.drf import ObjectNotExistsError, YAMLParser, YAMLRenderer
from airone.lib.http import http_get
from entity.api_v2.serializers import (
    EntityAttrNameSerializer,
    EntityCreateSerializer,
    EntityDetailSerializer,
    EntityHistorySerializer,
    EntityImportExportRootSerializer,
    EntityListSerializer,
    EntityUpdateSerializer,
)
from entity.models import Entity, EntityAttr
from entry.api_v2.serializers import EntryBaseSerializer, EntryCreateSerializer
from entry.models import Entry
from job.models import Job
from user.models import History, User


@http_get
def history(request, pk):
    if not Entity.objects.filter(id=pk).exists():
        return HttpResponse("Failed to get entity of specified id", status=400)

    # entity to be editted is given by url
    entity = Entity.objects.get(id=pk)
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
            "create": serializers.Serializer,
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

    @extend_schema(request=EntityCreateSerializer)
    def create(self, request, *args, **kwargs):
        user: User = request.user

        serializer = EntityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = Job.new_create_entity_v2(user, None, params=serializer.validated_data)
        job.run()

        return Response(status=status.HTTP_202_ACCEPTED)

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
    ordering_fields = ["name", "updated_time"]
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
        # return entity.history.all()

        attrs = entity.attrs.all()

        entity_histories = History.objects.filter(target_obj=entity, is_detail=False)
        entity_attr_histories = History.objects.filter(target_obj__in=attrs, is_detail=True)

        return entity_histories.union(entity_attr_histories).order_by("-time")


class EntityImportAPI(generics.GenericAPIView):
    parser_classes = [YAMLParser]
    serializer_class = serializers.Serializer

    def post(self, request):
        import_datas = request.data
        serializer = EntityImportExportRootSerializer(
            data=import_datas, context={"request": self.request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response()


class EntityExportAPI(generics.RetrieveAPIView):
    serializer_class = EntityImportExportRootSerializer
    renderer_classes = [YAMLRenderer]

    def get_object(self):
        user: User = self.request.user
        entities = get_permitted_objects(user, Entity, ACLType.Readable)
        attrs = get_permitted_objects(user, EntityAttr, ACLType.Readable)

        return {
            "Entity": entities,
            "EntityAttr": attrs,
        }


@extend_schema(
    parameters=[
        OpenApiParameter("entity_ids", OpenApiTypes.STR, OpenApiParameter.QUERY),
    ],
)
class EntityAttrNameAPI(generics.GenericAPIView):
    serializer_class = EntityAttrNameSerializer

    def get_queryset(self):
        entity_ids = list(filter(None, self.request.query_params.get("entity_ids", "").split(",")))

        if len(entity_ids) == 0:
            return (
                EntityAttr.objects.filter(is_active=True)
                .values_list("name", flat=True)
                .order_by("name")
                .distinct()
            )
        else:
            entities = Entity.objects.filter(id__in=entity_ids, is_active=True)
            if len(entity_ids) != len(entities):
                # the case invalid entity-id was specified
                raise ValidationError("Target Entity doesn't exist")
            else:
                return (
                    # filter only names appear in all specified entities
                    EntityAttr.objects.filter(parent_entity__in=entities, is_active=True)
                    .values("name")
                    .annotate(count=Count("name"))
                    .filter(count=len(entity_ids))
                    .values_list("name", flat=True)
                    .order_by("name")
                )

    def get(self, request):
        queryset = self.get_queryset()
        serializer: Serializer = self.get_serializer(queryset)
        return Response(serializer.data)
