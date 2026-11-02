import copy
import logging
from typing import Any, List, cast

from django.db.models import F, OuterRef, Prefetch, QuerySet, Subquery
from django.db.models.functions import Lower
from django.http import Http404, HttpRequest
from django.http.response import HttpResponse, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, generics, serializers, status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from airone.lib.acl import ACLType
from airone.lib.configuration_export import ConfigurationExportAPI
from airone.lib.drf import EntryIsNotEmptyError, ObjectNotExistsError, YAMLParser
from airone.lib.http import http_get
from airone.lib.plugin_dispatch import PluginOverrideMixin
from airone.lib.text import normalize_search_text
from airone.lib.types import AttrType
from entity.api_v2.serializers import (
    EntityAttrNameSerializer,
    EntityCreateSerializer,
    EntityDetailSerializer,
    EntityDiffQuerySerializer,
    EntityDiffSerializer,
    EntityHistorySerializer,
    EntityImportExportRootSerializer,
    EntityListSerializer,
    EntityUpdateSerializer,
)
from entity.models import Entity, EntityAttr
from entry.api_v2.serializers import EntryBaseSerializer, EntryCreateSerializer
from entry.models import Attribute, AttributeValue, Entry
from job.api_v2.serializers import ImportPreviewJobSerializer
from job.models import Job
from user.models import History, User

logger = logging.getLogger(__name__)


# distutils.util.strtoboolの代替実装
def strtobool(val: str) -> int:
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
def history(request: HttpRequest, pk: int) -> HttpResponse:
    user = cast(User, request.user)

    entity = Entity.objects.filter(id=pk).first()
    if entity is None:
        return HttpResponse("Failed to get entity of specified id", status=400)

    if not user.has_permission(entity, ACLType.Readable):
        return HttpResponse("You don't have permission to access this object", status=403)

    # Entity to be edited is given by URL
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
    def has_permission(self, request: Request, view: APIView) -> bool:
        permissions = {
            "list": ACLType.Readable,
            "create": ACLType.Writable,
        }

        # Only ViewSets expose the resolved action name. When plain APIViews
        # (which have no action) reach this permission check, fall through.
        action = getattr(view, "action", None)
        permission = permissions.get(action) if action is not None else None
        if not permission:
            return True

        # IsAuthenticated is combined ahead of us so we only see authenticated Users.
        user = cast(User, request.user)
        if user.is_readonly and permission > ACLType.Readable:
            return False

        entity_id = view.kwargs.get("pk") or view.kwargs.get("entity_id")
        if not entity_id:
            return True

        # Stash the fetched entity on the view for the object-permission phase to
        # avoid a second DB round-trip. django-stubs cannot see this dynamic attr,
        # so opt out at the two access sites with narrow ignores.
        if not hasattr(view, "_pagoda_context"):
            view._pagoda_context = {}  # type: ignore[attr-defined]

        entity: Entity | None = view._pagoda_context.get("entity")  # type: ignore[attr-defined]
        if not entity or entity.id != entity_id:
            entity = Entity.objects.filter(id=entity_id, is_active=True).first()
            view._pagoda_context["entity"] = entity  # type: ignore[attr-defined]

        if entity and not user.has_permission(entity, permission):
            return False

        return True

    def has_object_permission(self, request: Request, view: APIView, obj: Entity) -> bool:
        permissions = {
            "retrieve": ACLType.Readable,
            "update": ACLType.Writable,
            "destroy": ACLType.Full,
        }

        action = getattr(view, "action", None)
        permission = permissions.get(action) if action is not None else None
        if not permission:
            return True

        user = cast(User, request.user)
        if not user.has_permission(obj, permission):
            return False

        return True


class NameCaseInsensitiveSearchFilter(filters.SearchFilter):
    def get_search_fields(self, view: APIView, request: Request) -> list[str]:
        return ["name_lower"]

    def get_search_terms(self, request: Request) -> list[str]:
        return [term.lower() for term in super().get_search_terms(request)]

    def filter_queryset(self, request: Request, queryset: Any, view: APIView) -> Any:
        terms = self.get_search_terms(request)
        if not terms:
            return queryset

        normalized_terms = [normalize_search_text(term) for term in terms]
        return [
            entity
            for entity in queryset
            if all(term in normalize_search_text(entity.name) for term in normalized_terms)
        ]


@extend_schema(
    parameters=[
        OpenApiParameter("is_toplevel", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
    ],
)
class EntityAPI(viewsets.ModelViewSet[Entity]):
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticated & EntityPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, NameCaseInsensitiveSearchFilter]
    search_fields = ["name"]
    ordering = ["name"]

    def get_serializer_class(self) -> type[serializers.Serializer[Any]]:
        serializer: dict[str, type[serializers.Serializer[Any]]] = {
            "list": EntityListSerializer,
            "create": EntityCreateSerializer,
            "update": EntityUpdateSerializer,
        }
        return serializer.get(self.action, EntityDetailSerializer)

    def get_queryset(self) -> QuerySet[Entity]:
        is_toplevel = self.request.query_params.get("is_toplevel", None)

        filter_condition: dict[str, Any] = {"is_active": True}
        exclude_condition: dict[str, Any] = {}

        if is_toplevel is not None:
            if strtobool(is_toplevel):
                filter_condition["status"] = F("status").bitor(Entity.STATUS_TOP_LEVEL)
            else:
                exclude_condition["status"] = F("status").bitor(Entity.STATUS_TOP_LEVEL)

        return (
            Entity.objects.filter(**filter_condition)
            .exclude(**exclude_condition)
            .annotate(name_lower=Lower("name"))
        )

    @extend_schema(request=EntityCreateSerializer, responses={202: None})
    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        # IsAuthenticated permission is enforced upstream, so request.user is a User.
        user = cast(User, request.user)

        serializer = EntityCreateSerializer(data=request.data, context={"_user": user})
        serializer.is_valid(raise_exception=True)
        job_params = copy.deepcopy(serializer.validated_data)
        entity = serializer.create(serializer.validated_data)

        job = Job.new_create_entity_v2(user, entity, params=job_params)
        job.run()

        return Response(status=status.HTTP_202_ACCEPTED)

    @extend_schema(request=EntityUpdateSerializer, responses={202: None})
    def update(self, request: Request, *args: object, **kwargs: object) -> Response:
        user = cast(User, request.user)
        entity: Entity = self.get_object()

        serializer = EntityUpdateSerializer(
            instance=entity, data=request.data, context={"_user": user}
        )
        serializer.is_valid(raise_exception=True)
        job_params = copy.deepcopy(serializer.validated_data)
        serializer.update(entity, serializer.validated_data)

        job = Job.new_edit_entity_v2(user, entity, params=job_params)
        job.run()

        return Response(status=status.HTTP_202_ACCEPTED)

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
        user = cast(User, request.user)
        entity: Entity = self.get_object()

        if not entity.is_active:
            raise ObjectNotExistsError("specified entity has already been deleted")

        if Entry.objects.filter(schema=entity, is_active=True).exists():
            raise EntryIsNotEmptyError(
                "cannot delete Entity because one or more Entries are not deleted"
            )

        job = Job.new_delete_entity_v2(user, entity, params=request.data)
        job.run()

        return Response(status=status.HTTP_202_ACCEPTED)


class AliasSearchFilter(filters.SearchFilter):
    def get_search_fields(self, view: APIView, request: Request) -> list[str]:
        original_fields: list[str] = ["name_lower"]

        # update search_fields when "with_alias" parameter was specified
        # to consier aliases that are related with target item
        # filtered by specified "search" parameter
        if request.query_params.get("with_alias"):
            return original_fields + ["aliases_name_lower"]
        else:
            return original_fields

    def get_search_terms(self, request: Request) -> list[str]:
        return [term.lower() for term in super().get_search_terms(request)]

    def filter_queryset(self, request: Request, queryset: Any, view: APIView) -> Any:
        terms = self.get_search_terms(request)
        if not terms:
            return queryset

        normalized_terms = [normalize_search_text(term) for term in terms]
        with_alias = bool(request.query_params.get("with_alias"))
        return [
            entry
            for entry in queryset
            if all(
                any(
                    term in normalize_search_text(value)
                    for value in (
                        [entry.name]
                        + ([alias.name for alias in entry.aliases.all()] if with_alias else [])
                    )
                )
                for term in normalized_terms
            )
        ]


@extend_schema(
    parameters=[
        OpenApiParameter("with_alias", OpenApiTypes.STR, OpenApiParameter.QUERY),
    ],
)
class EntityEntryAPI(PluginOverrideMixin, viewsets.ModelViewSet[Entry]):
    """Entity Entry API ViewSet with plugin override support.

    Plugin overrides are automatically handled by PluginOverrideMixin.
    Configure overrides via BACKEND_PLUGIN_ENTITY_OVERRIDES environment variable.
    """

    queryset = Entry.objects.all()
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated & EntityPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, AliasSearchFilter]
    filterset_fields = ["is_active"]
    ordering_fields = ["name", "updated_time"]
    search_fields = ["name"]

    def get_serializer_class(self) -> type[serializers.Serializer[Any]]:
        serializer: dict[str, type[serializers.Serializer[Any]]] = {
            "create": EntryCreateSerializer,
        }
        return serializer.get(self.action, EntryBaseSerializer)

    def get_queryset(self) -> QuerySet[Entry]:
        entity_id = self.kwargs.get("entity_id")
        if entity_id is None:
            raise Http404
        entity = Entity.objects.filter(id=entity_id, is_active=True).first()
        if not entity:
            raise Http404
        qs = (
            self.queryset.filter(schema=entity).select_related("schema").prefetch_related("aliases")
        )
        if self.request.query_params.get("with_alias"):
            qs = qs.annotate(name_lower=Lower("name"), aliases_name_lower=Lower("aliases__name"))
        else:
            qs = qs.annotate(name_lower=Lower("name"))
        return qs

    @extend_schema(request=EntryCreateSerializer, responses={202: None})
    def create(self, request: Request, entity_id: int) -> Response:
        entity = Entity.objects.filter(id=entity_id).first()
        if entity:
            response = self._dispatch_override(request, "create", entity.id, entity)
            if response is not None:
                return response

        user = cast(User, request.user)

        # Set schema to entity_id and let the serializer validate it
        # This allows proper validation error response for non-existent entities
        request.data["schema"] = entity_id

        serializer = EntryCreateSerializer(data=request.data, context={"_user": user})
        serializer.is_valid(raise_exception=True)

        job = Job.new_create_entry_v2(user, None, params=request.data)
        job.run()

        return Response(status=status.HTTP_202_ACCEPTED)


class EntityHistoryAPI(viewsets.ReadOnlyModelViewSet[History]):
    serializer_class = EntityHistorySerializer
    permission_classes = [IsAuthenticated & EntityPermission]
    pagination_class = LimitOffsetPagination

    def get_queryset(self) -> QuerySet[History]:
        entity_id = self.kwargs.get("entity_id")
        if entity_id is None:
            raise Http404
        entity = Entity.objects.get(id=entity_id)

        attrs = entity.attrs.all()

        entity_histories = History.objects.filter(target_obj=entity, is_detail=False)
        entity_attr_histories = History.objects.filter(target_obj__in=attrs, is_detail=True)

        return entity_histories.union(entity_attr_histories).order_by("-time")

    def list(self, request: Request, *args: object, **kwargs: object) -> Response:
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
        if entity_id is None:
            raise Http404
        entity = Entity.objects.get(id=entity_id)
        historical_cache = self._build_historical_cache(entity, cached_histories)

        # Build serializer context with historical caches
        serializer_context = {
            "request": request,
            "historical_cache": historical_cache,
        }

        # paginate_queryset accepts pre-fetched sequences too; drf-stubs annotates it
        # tighter than the runtime accepts.
        page = self.paginate_queryset(cached_histories)  # type: ignore[arg-type]
        if page is not None:
            serializer = self.get_serializer(page, many=True, context=serializer_context)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(cached_histories, many=True, context=serializer_context)
        return Response(serializer.data)

    def _build_historical_cache(
        self, entity: Entity, histories: List[History]
    ) -> dict[str, List[Any]]:
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


class EntityImportAPI(generics.GenericAPIView[Entity]):
    parser_classes = [YAMLParser]
    # EntityImportExportRootSerializer is Serializer[dict], not Serializer[Entity],
    # so the tighter drf-stubs annotation on serializer_class does not fit here.
    serializer_class = EntityImportExportRootSerializer  # type: ignore[assignment]

    @extend_schema(responses={200: None})
    def post(self, request: Request) -> Response:
        user = cast(User, request.user)
        if user.is_readonly:
            return Response(status=status.HTTP_403_FORBIDDEN)

        import_datas = request.data
        serializer = EntityImportExportRootSerializer(
            data=import_datas, context={"request": self.request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response()


class EntityImportPreviewAPI(generics.GenericAPIView[Entity]):
    """Start a job that reports what an import file would change.

    Previewing walks the same rows the import walks, so it costs the same: it is
    handed to a worker and this endpoint returns the job to poll, rather than
    holding a request open for as long as the import would take. That also means
    a preview has no row limit -- a file too big to preview in a request is
    exactly the file whose preview is worth waiting for.

    The preview stays optional: clients may post straight to ``EntityImportAPI``.
    """

    parser_classes = [YAMLParser]
    serializer_class = ImportPreviewJobSerializer  # type: ignore[assignment]

    @extend_schema(
        request=EntityImportExportRootSerializer,
        responses={202: ImportPreviewJobSerializer},
    )
    def post(self, request: Request) -> Response:
        user = cast(User, request.user)
        if user.is_readonly:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = EntityImportExportRootSerializer(
            data=request.data, context={"request": self.request}
        )
        serializer.is_valid(raise_exception=True)

        job = Job.new_import_entity_preview(user, serializer.validated_data)
        job.run()

        return Response({"job_id": job.id}, status=status.HTTP_202_ACCEPTED)


class EntityExportAPI(ConfigurationExportAPI):
    export_kind = "entity"


@extend_schema(
    parameters=[
        OpenApiParameter("entity_ids", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("referral_attr", OpenApiTypes.STR, OpenApiParameter.QUERY),
    ],
)
class EntityAttrNameAPI(generics.GenericAPIView[EntityAttr]):
    # EntityAttrNameSerializer is a ListSerializer producing plain dicts, not
    # EntityAttr instances, so the tighter serializer_class annotation does not fit.
    serializer_class = EntityAttrNameSerializer  # type: ignore[assignment]

    def get_queryset(self) -> list[dict[str, int | str]]:  # type: ignore[override]
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
                entity_attrs.values_list("name", "id", "type", flat=False)
                .order_by("name")
                .distinct()
            )
        # single parent_entity case
        else:
            values_list = entity_attrs.values_list("name", "id", "type", flat=False).order_by(
                "index", "pk"
            )

        return [
            {
                "id": attrid,
                "name": attrname,
                "type": attrtype,
            }
            for (attrname, attrid, attrtype) in values_list
        ]

    def get(self, request: Request) -> Response:
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


class EntityDiffAPI(generics.GenericAPIView[Entity]):
    """Report entries whose attribute value differs between two points in time."""

    serializer_class = EntityDiffQuerySerializer

    @staticmethod
    def _value_of(attrv: AttributeValue | None) -> Any:
        if attrv is None:
            return None
        # with_metainfo wraps the value as {"type": ..., "value": ...}; keep only the value
        value = attrv.get_value(with_metainfo=True, serialize=True)["value"]

        # An unset value is represented differently per type; normalize it to None so that
        # it compares equal to "no value" (e.g. an attribute that has never been set).
        data_type = attrv.data_type
        if data_type & AttrType._ARRAY:
            # array_* and multi-select
            is_empty = value == [] or [x for x in value if x is not None] == []
        elif data_type in (AttrType.NAMED_OBJECT, AttrType.NAMED_OBJECT_BOOLEAN):
            is_empty = value == {"": None}
        elif data_type == AttrType.DATE:
            is_empty = value is None or value == "None"
        else:
            is_empty = False

        return None if is_empty else value

    @extend_schema(
        parameters=[EntityDiffQuerySerializer],
        responses=EntityDiffSerializer,
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = cast("User", request.user)
        query = EntityDiffQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        model = query.validated_data["model"]
        attr_names = list(dict.fromkeys(query.validated_data["attr"]))
        t0 = query.validated_data["t0"]
        t1 = query.validated_data["t1"]

        entity = Entity.objects.filter(name=model, is_active=True).first()
        if entity is None or not user.has_permission(entity, ACLType.Readable):
            raise NotFound("Target Entity doesn't exist")
        entity_attrs = {
            ea.name: ea
            for ea in EntityAttr.objects.filter(
                parent_entity=entity, name__in=attr_names, is_active=True
            )
        }
        if any(name not in entity_attrs for name in attr_names):
            raise NotFound("Target attribute doesn't exist in the Entity")

        # AttributeValue accumulates a row per update, so never load the history. The id of
        # the value in effect at t0/t1 is resolved by index-backed subqueries (one row each).
        def latest_value_id(at: Any) -> Subquery:
            return Subquery(
                AttributeValue.objects.filter(
                    parent_attr=OuterRef("pk"), parent_attrv__isnull=True, created_time__lte=at
                )
                .order_by("-created_time", "-id")
                .values("id")[:1]
            )

        attrs = (
            Attribute.objects.filter(
                schema__in=entity_attrs.values(), parent_entry__is_active=True, is_active=True
            )
            .select_related("parent_entry", "schema")
            .annotate(attrv_id_t0=latest_value_id(t0), attrv_id_t1=latest_value_id(t1))
        )
        attr_order = {name: i for i, name in enumerate(attr_names)}

        # Drop attributes whose value did not change (same row at both points, or none at all)
        # and the ones the user may not read, before loading any value.
        targets = []
        for attr in sorted(attrs, key=lambda a: (attr_order[a.schema.name], a.id)):
            id_t0: int | None = attr.attrv_id_t0
            id_t1: int | None = attr.attrv_id_t1
            if id_t0 == id_t1:
                continue
            if not user.has_permission(
                attr.parent_entry, ACLType.Readable
            ) or not user.has_permission(attr, ACLType.Readable):
                continue
            targets.append((attr, id_t0, id_t1))

        attrvs = (
            AttributeValue.objects.select_related("referral", "group", "role")
            .prefetch_related(
                Prefetch(
                    "data_array",
                    queryset=AttributeValue.objects.select_related("referral", "group", "role"),
                )
            )
            .in_bulk({i for _, id_t0, id_t1 in targets for i in (id_t0, id_t1) if i is not None})
        )

        # entry id -> item, so that every entry appears once with all of its differing attrs
        items: dict[int, dict[str, Any]] = {}
        for attr, id_t0, id_t1 in targets:
            value_t0 = self._value_of(attrvs.get(id_t0) if id_t0 is not None else None)
            value_t1 = self._value_of(attrvs.get(id_t1) if id_t1 is not None else None)
            if value_t0 == value_t1:
                continue
            entry = attr.parent_entry
            item = items.setdefault(entry.id, {"id": entry.id, "name": entry.name, "attrs": []})
            item["attrs"].append(
                {
                    "id": attr.id,
                    "name": attr.schema.name,
                    "type": attr.schema.type,
                    "value_t0": value_t0,
                    "value_t1": value_t1,
                }
            )

        return Response({"count": len(items), "items": list(items.values())})
