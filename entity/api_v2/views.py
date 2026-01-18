from typing import List

from django.db.models import F
from django.http import Http404
from django.http.response import HttpResponse, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, generics, serializers, status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

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


# distutils.util.strtoboolの代替実装
def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return 1
    elif val in ("n", "no", "f", "false", "off", "0"):
        return 0
    else:
        raise ValueError(f"Invalid truth value {val}")


@http_get
def history(request, pk: int) -> HttpResponse:
    if not Entity.objects.filter(id=pk).exists():
        return HttpResponse("Failed to get entity of specified id", status=400)

    # Entity to be edited is given by URL
    entity = Entity.objects.get(id=pk)
    histories = (
        History.objects.filter(target_obj=entity, is_detail=False)
        .select_related("user", "target_obj")
        .prefetch_related("details__user", "details__target_obj")
        .order_by("-time")
    )

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
    def has_permission(self, request: Request, view) -> bool:
        permissions = {
            "list": ACLType.Readable,
            "create": ACLType.Writable,
        }

        permission = permissions.get(view.action)
        if not permission:
            return True

        entity_id = view.kwargs.get("pk") or view.kwargs.get("entity_id")
        if not entity_id:
            return True

        if not hasattr(view, "_pagoda_context"):
            view._pagoda_context = {}

        entity: Entity | None = view._pagoda_context.get("entity")
        if not entity or entity.id != entity_id:
            entity = Entity.objects.filter(id=entity_id, is_active=True).first()
            view._pagoda_context["entity"] = entity

        if entity and not request.user.has_permission(entity, permission):
            return False

        return True

    def has_object_permission(self, request: Request, view, obj) -> bool:
        permissions = {
            "retrieve": ACLType.Readable,
            "update": ACLType.Writable,
            "destroy": ACLType.Full,
        }

        permission = permissions.get(view.action)
        if not permission:
            return True

        if not request.user.has_permission(obj, permission):
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

    @extend_schema(request=EntityCreateSerializer)
    def create(self, request: Request, *args, **kwargs) -> Response:
        user: User = request.user

        serializer = EntityCreateSerializer(data=request.data, context={"_user": user})
        serializer.is_valid(raise_exception=True)
        entity = serializer.create(serializer.validated_data)

        job = Job.new_create_entity_v2(user, entity, params=request.data)
        job.run()

        return Response(status=status.HTTP_202_ACCEPTED)

    @extend_schema(request=EntityUpdateSerializer)
    def update(self, request: Request, *args, **kwargs) -> Response:
        user: User = request.user
        entity: Entity = self.get_object()

        serializer = EntityUpdateSerializer(
            instance=entity, data=request.data, context={"_user": user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.update(entity, serializer.validated_data)

        job = Job.new_edit_entity_v2(user, entity, params=request.data)
        job.run()

        return Response(status=status.HTTP_202_ACCEPTED)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        user: User = request.user
        entity: Entity = self.get_object()

        if not entity.is_active:
            raise ObjectNotExistsError("specified entity has already been deleted")

        if Entry.objects.filter(schema=entity, is_active=True).exists():
            raise ValidationError(
                "cannot delete Entity because one or more Entries are not deleted"
            )

        job = Job.new_delete_entity_v2(user, entity, params=request.data)
        job.run()

        return Response(status=status.HTTP_202_ACCEPTED)


class AliasSearchFilter(filters.SearchFilter):
    def get_search_fields(self, view, request):
        original_fields = super().get_search_fields(view, request)

        # update search_fields when "with_alias" parameter was specified
        # to consier aliases that are related with target item
        # filtered by specified "search" parameter
        if request.query_params.get("with_alias"):
            return original_fields + ["aliases__name"]
        else:
            return original_fields


@extend_schema(
    parameters=[
        OpenApiParameter("with_alias", OpenApiTypes.STR, OpenApiParameter.QUERY),
    ],
)
class EntityEntryAPI(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated & EntityPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, AliasSearchFilter]
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
        return (
            self.queryset.filter(schema=entity).select_related("schema").prefetch_related("aliases")
        )

    @extend_schema(request=EntryCreateSerializer)
    def create(self, request: Request, entity_id: int) -> Response:
        user: User = request.user
        request.data["schema"] = entity_id

        serializer = EntryCreateSerializer(data=request.data, context={"_user": user})
        serializer.is_valid(raise_exception=True)

        job = Job.new_create_entry_v2(user, None, params=request.data)
        job.run()

        return Response(status=status.HTTP_202_ACCEPTED)


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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Solve N+1 problem by prefetching related objects
        # Trade-off: Uses more memory and 2 queries instead of 1, but eliminates N+1 queries
        history_ids = list(queryset.values_list("id", flat=True))

        # Bulk fetch user and target_obj relations to avoid N+1 queries in serialization
        histories_with_relations = History.objects.filter(id__in=history_ids).select_related(
            "user", "target_obj"
        )

        # Create ID-based mapping for efficient lookup during serialization
        history_cache = {h.id: h for h in histories_with_relations}

        # Replace queryset results with cached objects and maintain time ordering
        # Note: Sorting is done in Python, which may be slower for very large datasets
        cached_histories = [history_cache[h_id] for h_id in history_ids if h_id in history_cache]
        cached_histories.sort(key=lambda h: h.time, reverse=True)

        # Build simple-history caches for diff calculation
        entity_id = self.kwargs.get("entity_id")
        entity = Entity.objects.get(id=entity_id)
        historical_cache = self._build_historical_cache(entity, cached_histories)

        # Build serializer context with historical caches
        serializer_context = {
            "request": request,
            "historical_cache": historical_cache,
        }

        page = self.paginate_queryset(cached_histories)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context=serializer_context)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(cached_histories, many=True, context=serializer_context)
        return Response(serializer.data)

    def _build_historical_cache(self, entity: Entity, histories: List[History]) -> dict:
        """
        Build cache for simple-history records to avoid N+1 queries.

        Returns a dict with keys like:
        - "entity_{id}": list of HistoricalEntity records
        - "attr_{id}": list of HistoricalEntityAttr records
        """
        historical_cache = {}

        # Cache Entity historical records
        entity_historicals = list(
            entity.history.select_related("history_user").order_by("-history_date")
        )
        historical_cache[f"entity_{entity.id}"] = entity_historicals

        # Collect all EntityAttr IDs from the histories
        attr_ids = set()
        for h in histories:
            if h.operation & History.TARGET_ATTR:
                attr_ids.add(h.target_obj_id)

        # Cache EntityAttr historical records
        for attr_id in attr_ids:
            try:
                attr = EntityAttr.objects.get(id=attr_id)
                attr_historicals = list(
                    attr.history.select_related("history_user").order_by("-history_date")
                )
                historical_cache[f"attr_{attr_id}"] = attr_historicals
            except EntityAttr.DoesNotExist:
                # Attr may have been deleted, but we can still try to get historical records
                # via the historical model directly
                attr_historicals = list(
                    EntityAttr.history.filter(id=attr_id)
                    .select_related("history_user")
                    .order_by("-history_date")
                )
                historical_cache[f"attr_{attr_id}"] = attr_historicals

        return historical_cache


class EntityImportAPI(generics.GenericAPIView):
    parser_classes = [YAMLParser]
    serializer_class = EntityImportExportRootSerializer

    def post(self, request: Request) -> Response:
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

    def get_object(self) -> dict:
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
        OpenApiParameter("referral_attr", OpenApiTypes.STR, OpenApiParameter.QUERY),
    ],
)
class EntityAttrNameAPI(generics.GenericAPIView):
    serializer_class = EntityAttrNameSerializer

    def get_queryset(self):
        entity_ids = list(filter(None, self.request.query_params.get("entity_ids", "").split(",")))
        referral_attr = self.request.query_params.get("referral_attr")

        entity_attrs = EntityAttr.objects.filter(is_active=True)
        if len(entity_ids) != 0:
            entities = Entity.objects.filter(id__in=entity_ids, is_active=True)
            if len(entity_ids) != len(entities):
                # the case invalid entity-id was specified
                raise NotFound("Target Entity doesn't exist")

            # filter only names appear in all specified entities
            entity_attrs = entity_attrs.filter(parent_entity__in=entities)

        if referral_attr:
            referral_entity_ids = (
                entity_attrs.filter(name=referral_attr)
                .exclude(referral__id__isnull=True)
                .values_list("referral", flat=True)
                .distinct()
            )
            entity_attrs = EntityAttr.objects.filter(
                parent_entity__in=referral_entity_ids, is_active=True
            )

        # multiple parent_entity case
        if len(entity_attrs.values_list("parent_entity_id", flat=True).distinct()) > 1:
            values_list = (
                entity_attrs.values_list("name", "id", flat=False).order_by("name").distinct()
            )
        # single parent_entity case
        else:
            values_list = entity_attrs.values_list("name", "id", flat=False).order_by("index", "pk")

        return [
            {
                "id": attrid,
                "name": attrname,
            }
            for (attrname, attrid) in values_list
        ]

    def get(self, request: Request) -> Response:
        queryset = self.get_queryset()
        serializer: serializers.Serializer = self.get_serializer(queryset)
        return Response(serializer.data)
