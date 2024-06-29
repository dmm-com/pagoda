import re
import time
from copy import deepcopy
from datetime import datetime, timedelta

from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, serializers, status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from airone.exceptions import ElasticsearchException
from airone.lib import advancedsearch, custom_view
from airone.lib.acl import ACLType
from airone.lib.drf import (
    DuplicatedObjectExistsError,
    FrequentImportError,
    IncorrectTypeError,
    ObjectNotExistsError,
    RequiredParameterError,
    YAMLParser,
)
from airone.lib.elasticsearch import AdvancedSearchResultValue, AttrHint
from airone.lib.types import AttrType
from api_v1.entry.serializer import EntrySearchChainSerializer
from entity.models import Entity, EntityAttr
from entry.api_v2.pagination import EntryReferralPagination
from entry.api_v2.serializers import (
    AdvancedSearchResultExportSerializer,
    AdvancedSearchResultSerializer,
    AdvancedSearchSerializer,
    EntryAttributeValueRestoreSerializer,
    EntryBaseSerializer,
    EntryCopySerializer,
    EntryExportSerializer,
    EntryHistoryAttributeValueSerializer,
    EntryImportSerializer,
    EntryRetrieveSerializer,
    EntryUpdateSerializer,
    GetEntryAttrReferralSerializer,
)
from entry.models import Attribute, AttributeValue, Entry
from entry.settings import CONFIG
from entry.settings import CONFIG as ENTRY_CONFIG
from entry.tasks import ExportTaskParams
from group.models import Group
from job.models import Job, JobOperation, JobStatus
from role.models import Role
from user.models import User


class EntryPermission(BasePermission):
    def has_object_permission(self, request: Request, view, obj) -> bool:
        user: User = request.user
        permisson = {
            "retrieve": ACLType.Readable,
            "update": ACLType.Writable,
            "destroy": ACLType.Writable,
            "restore": ACLType.Writable,
            "copy": ACLType.Writable,
            "list": ACLType.Readable,  # histories
        }

        if not user.has_permission(obj, permisson.get(view.action)):
            return False

        return True


class EntryAPI(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    permission_classes = [IsAuthenticated & EntryPermission]
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        serializer = {
            "retrieve": EntryRetrieveSerializer,
            "update": serializers.Serializer,
            "copy": EntryCopySerializer,
            "list": EntryHistoryAttributeValueSerializer,
        }
        return serializer.get(self.action, EntryBaseSerializer)

    @extend_schema(request=EntryUpdateSerializer)
    def update(self, request: Request, *args, **kwargs) -> Response:
        user: User = request.user
        entry: Entry = self.get_object()

        serializer = EntryUpdateSerializer(
            instance=entry, data=request.data, context={"_user": user}
        )
        serializer.is_valid(raise_exception=True)

        job = Job.new_edit_entry_v2(user, entry, params=request.data)
        job.run()

        return Response(status=status.HTTP_202_ACCEPTED)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        entry: Entry = self.get_object()
        if not entry.is_active:
            raise ObjectNotExistsError("specified entry has already been deleted")

        user: User = request.user

        job: Job = Job.new_delete_entry_v2(user, entry)
        job.run()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def restore(self, request: Request, *args, **kwargs) -> Response:
        entry: Entry = self.get_object()

        if entry.is_active:
            raise ObjectNotExistsError("specified entry has not deleted")

        # checks that a same name entry corresponding to the entity is existed, or not.
        if Entry.objects.filter(
            schema=entry.schema, name=re.sub(r"_deleted_[0-9_]*$", "", entry.name), is_active=True
        ).exists():
            raise DuplicatedObjectExistsError("specified entry has already exist other")

        user: User = request.user

        if custom_view.is_custom("before_restore_entry_v2", entry.schema.name):
            custom_view.call_custom("before_restore_entry_v2", entry.schema.name, user, entry)

        entry.set_status(Entry.STATUS_CREATING)

        # restore entry
        entry.restore()

        if custom_view.is_custom("after_restore_entry_v2", entry.schema.name):
            custom_view.call_custom("after_restore_entry_v2", entry.schema.name, user, entry)

        # remove status flag which is set before calling this
        entry.del_status(Entry.STATUS_CREATING)

        # Send notification to the webhook URL
        job_notify_event = Job.new_notify_create_entry(user, entry)
        job_notify_event.run()

        return Response({}, status=status.HTTP_201_CREATED)

    def copy(self, request: Request, *args, **kwargs) -> Response:
        src_entry: Entry = self.get_object()

        if not src_entry.is_active:
            raise ObjectNotExistsError("specified entry is not active")

        # validate post parameter
        serializer = self.get_serializer(src_entry, data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO Conversion to support the old UI
        params = {
            "new_name_list": request.data["copy_entry_names"],
            "post_data": request.data,
        }

        # run copy job
        job = Job.new_copy(request.user, src_entry, text="Preparing to copy entry", params=params)
        job.run()

        return Response({}, status=status.HTTP_200_OK)

    # histories view
    def list(self, request: Request, *args, **kwargs) -> Response:
        user: User = self.request.user
        entry: Entry = self.get_object()

        # check permission for attribute
        target_attrs = []
        for attr in entry.attrs.filter(schema__is_active=True):
            if user.has_permission(attr, ACLType.Readable):
                target_attrs.append(attr)

        self.queryset = (
            AttributeValue.objects.filter(
                parent_attr__in=target_attrs,
                parent_attrv__isnull=True,
            )
            .order_by("-created_time")
            .select_related("parent_attr")
        )

        return super(EntryAPI, self).list(request, *args, **kwargs)


@extend_schema(
    parameters=[
        OpenApiParameter("query", OpenApiTypes.STR, OpenApiParameter.QUERY),
    ],
)
class searchAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = EntryBaseSerializer

    def get_queryset(self):
        queryset = []
        query = self.request.query_params.get("query", None)

        if not query:
            return queryset

        results = Entry.search_entries_for_simple(query, limit=ENTRY_CONFIG.MAX_SEARCH_ENTRIES)
        return results["ret_values"]


class AdvancedSearchAPI(generics.GenericAPIView):
    serializer_class = AdvancedSearchSerializer
    """
    NOTE for now it's just copied from /api/v1/entry/search, but it should be
    rewritten with DRF components.
    """

    @extend_schema(
        request=AdvancedSearchSerializer,
        responses=AdvancedSearchResultSerializer,
    )
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        hint_entities = serializer.validated_data["entities"]
        hint_entry_name = serializer.validated_data["entry_name"]
        hint_attrs = serializer.validated_data["attrinfo"]
        hint_referral = serializer.validated_data.get("referral_name")
        has_referral = serializer.validated_data["has_referral"]
        is_output_all = serializer.validated_data["is_output_all"]
        is_all_entities = serializer.validated_data["is_all_entities"]
        entry_limit = serializer.validated_data["entry_limit"]
        entry_offset = serializer.validated_data["entry_offset"]
        join_attrs = serializer.validated_data.get("join_attrs", [])

        def _get_joined_resp(
            prev_results: list[AdvancedSearchResultValue], join_attr: dict
        ) -> tuple[bool, dict]:
            """
            This is a helper method for join_attrs that will get specified attr values
            that prev_result's ones refer to.
            """
            # set hint_entity_ids for joining Items search and get item names
            # that specified attribute refers
            item_names = []
            hint_entity_ids = []
            for result in prev_results:
                entity = Entity.objects.filter(id=result.entity["id"]).last()
                if entity is None:
                    continue

                attr = entity.attrs.filter(name=join_attr["name"], is_active=True).last()
                if attr is None:
                    continue

                if attr.type & AttrType.OBJECT:
                    # set hint Model ID
                    hint_entity_ids += [x.id for x in attr.referral.filter(is_active=True)]

                    # set Item name
                    attrinfo = result.attrs[join_attr["name"]]

                    if attr.type == AttrType.OBJECT and attrinfo["value"]["name"] not in item_names:
                        item_names.append(attrinfo["value"]["name"])

                    if attr.type == AttrType.NAMED_OBJECT:
                        for co_info in attrinfo["value"].values():
                            if co_info["name"] not in item_names:
                                item_names.append(co_info["name"])

                    if attr.type == AttrType.ARRAY_OBJECT:
                        for r in attrinfo["value"]:
                            item_names.append(r["name"])

                    if attr.type == AttrType.ARRAY_NAMED_OBJECT:
                        for r in attrinfo["value"]:
                            [co_info] = r.values()
                            item_names.append(co_info["name"])

            # set parameters to filter joining search results
            hint_attrs: list[AttrHint] = []
            for info in join_attr.get("attrinfo", []):
                hint_attrs.append(
                    {
                        "name": info["name"],
                        "keyword": info.get("keyword"),
                        "filter_key": info.get("filter_key"),
                    }
                )

            # search Items from elasticsearch to join
            return (
                # This represents whether user want to narrow down results by keyword of joined attr
                any(
                    [
                        x.get("keyword") or x.get("filter_key", 0) > 0
                        for x in join_attr.get("attrinfo", [])
                    ]
                ),
                Entry.search_entries(
                    request.user,
                    hint_entity_ids=list(set(hint_entity_ids)),  # this removes depulicated IDs
                    hint_attrs=hint_attrs,
                    limit=entry_limit,
                    entry_name="|".join(item_names),
                    hint_referral=None,
                    is_output_all=is_output_all,
                    hint_referral_entity_id=None,
                    offset=join_attr.get("offset", 0),
                ).dict(),
            )

        # === End of Function: _get_joined_resp() ===

        def _get_ref_id_from_es_result(attrinfo):
            if attrinfo["type"] == AttrType.OBJECT:
                if attrinfo.get("value") is not None:
                    return [attrinfo["value"].get("id")]

            if attrinfo["type"] == AttrType.NAMED_OBJECT:
                if attrinfo.get("value") is not None:
                    [ref_info] = attrinfo["value"].values()
                    return [ref_info.get("id")]

            if attrinfo["type"] == AttrType.ARRAY_OBJECT:
                return [x.get("id") for x in attrinfo["value"]]

            if attrinfo["type"] == AttrType.ARRAY_NAMED_OBJECT:
                return sum([[y["id"] for y in x.values()] for x in attrinfo["value"]], [])

            return []

        # === End of Function: _get_ref_id_from_es_result() ===

        if not has_referral:
            hint_referral = None

        if is_all_entities:
            attr_names = [x["name"] for x in hint_attrs]
            hint_entities = list(
                EntityAttr.objects.filter(
                    name__in=attr_names, is_active=True, parent_entity__is_active=True
                )
                .order_by("parent_entity__name")
                .values_list("parent_entity__id", flat=True)
                .distinct()
            )
            if not hint_entities:
                return Response("Invalid value for attribute parameter", status=400)

        hint_entity_ids = []
        for hint_entity in hint_entities:
            entity = None
            if isinstance(hint_entity, int):
                entity = Entity.objects.filter(id=hint_entity, is_active=True).first()
            elif isinstance(hint_entity, str):
                if hint_entity.isnumeric():
                    entity = Entity.objects.filter(
                        Q(id=hint_entity) | Q(name=hint_entity), Q(is_active=True)
                    ).first()
                else:
                    entity = Entity.objects.filter(name=hint_entity, is_active=True).first()

            if entity and request.user.has_permission(entity, ACLType.Readable):
                hint_entity_ids.append(entity.id)

        # XXX experimental advanced search
        start_time = time.perf_counter()
        resp = advancedsearch.search_entries(
            user=request.user,
            entities=hint_entity_ids,
            attr_hints=hint_attrs,
            entry_name=hint_entry_name,
            hint_referral=hint_referral,
            is_output_all=is_output_all,
            limit=entry_limit,
            offset=entry_offset,
        )
        end_time = time.perf_counter()
        print(f"[Experimental Advanced Search] processing time: {(end_time - start_time):.6f} sec")

        start_time = time.perf_counter()
        Entry.search_entries(
            request.user,
            hint_entity_ids,
            hint_attrs,
            entry_limit,
            hint_entry_name,
            hint_referral,
            is_output_all,
            offset=entry_offset,
        )
        end_time = time.perf_counter()
        print(f"[Current Advanced Search] processing time: {(end_time - start_time):.6f} sec")

        # save total population number
        total_count = deepcopy(resp.ret_count)

        for join_attr in join_attrs:
            (will_filter_by_joined_attr, joined_resp) = _get_joined_resp(resp.ret_values, join_attr)
            # This is needed to set result as blank value
            blank_joining_info = {
                "%s.%s" % (join_attr["name"], k["name"]): {
                    "is_readable": True,
                    "type": AttrType.STRING,
                    "value": "",
                }
                for k in join_attr["attrinfo"]
            }

            # convert search result to dict to be able to handle it without loop
            joined_resp_info = {
                x["entry"]["id"]: {
                    "%s.%s" % (join_attr["name"], k): v
                    for k, v in x["attrs"].items()
                    if any(_x["name"] == k for _x in join_attr["attrinfo"])
                }
                for x in joined_resp["ret_values"]
            }

            # this inserts result to previous search result
            new_ret_values = []
            joined_ret_values = []
            for resp_result in resp.ret_values:
                # joining search result to original one
                ref_info = resp_result.attrs.get(join_attr["name"])

                # This get referral Item-ID from joined search result
                ref_list = _get_ref_id_from_es_result(ref_info)
                for ref_id in ref_list:
                    if ref_id and ref_id in joined_resp_info:  # type: ignore
                        # join valid value
                        resp_result.attrs |= joined_resp_info[ref_id]

                        # collect only the result that matches with keyword of joined_attr parameter
                        copied_result = deepcopy(resp_result)
                        new_ret_values.append(copied_result)
                        joined_ret_values.append(copied_result)

                    else:
                        # join EMPTY value
                        resp_result.attrs |= blank_joining_info  # type: ignore
                        joined_ret_values.append(deepcopy(resp_result))

                if len(ref_list) == 0:
                    # join EMPTY value
                    resp_result.attrs |= blank_joining_info  # type: ignore
                    joined_ret_values.append(deepcopy(resp_result))

            if will_filter_by_joined_attr:
                resp.ret_values = new_ret_values
                resp.ret_count = len(new_ret_values)
            else:
                resp.ret_values = joined_ret_values
                resp.ret_count = len(joined_ret_values)

        # convert field values to fit entry retrieve API data type, as a workaround.
        # FIXME should be replaced with DRF serializer etc
        for entry in resp.ret_values:
            for name, attr in entry.attrs.items():

                def _get_typed_value(type: int) -> str:
                    if type & AttrType._ARRAY:
                        if type & AttrType.STRING:
                            return "as_array_string"
                        elif type & AttrType._NAMED:
                            return "as_array_named_object"
                        elif type & AttrType.OBJECT:
                            return "as_array_object"
                        elif type & AttrType.GROUP:
                            return "as_array_group"
                        elif type & AttrType.ROLE:
                            return "as_array_role"
                    elif type & AttrType.STRING or type & AttrType.TEXT:
                        return "as_string"
                    elif type & AttrType._NAMED:
                        return "as_named_object"
                    elif type & AttrType.OBJECT:
                        return "as_object"
                    elif type & AttrType.BOOLEAN:
                        return "as_boolean"
                    elif type & AttrType.DATE:
                        return "as_string"
                    elif type & AttrType.GROUP:
                        return "as_group"
                    elif type & AttrType.ROLE:
                        return "as_role"
                    elif type & AttrType.DATETIME:
                        return "as_string"
                    raise IncorrectTypeError(f"unexpected type: {type}")

                entry.attrs[name] = {
                    "is_readable": attr["is_readable"],
                    "type": attr["type"],
                    "value": {
                        _get_typed_value(attr["type"]): attr.get("value", ""),
                    },
                }

                # "asString" is a string type and does not allow None
                if (
                    _get_typed_value(attr["type"]) == "as_string"
                    and entry.attrs[name]["value"]["as_string"] is None
                ):
                    entry.attrs[name]["value"]["as_string"] = ""

                # "asNamedObject", "as_array_named_object" converts types
                if _get_typed_value(attr["type"]) == "as_named_object":
                    value = entry.attrs[name]["value"]["as_named_object"]
                    entry.attrs[name]["value"]["as_named_object"] = {
                        "name": list(value.keys())[0],
                        "object": list(value.values())[0],
                    }

                if _get_typed_value(attr["type"]) == "as_array_named_object":
                    values = entry.attrs[name]["value"]["as_array_named_object"]
                    entry.attrs[name]["value"]["as_array_named_object"] = [
                        {
                            "name": list(value.keys())[0],
                            "object": list(value.values())[0],
                        }
                        for value in values
                    ]

        serializer = AdvancedSearchResultSerializer(
            data={
                "count": resp.ret_count,
                "values": [x.dict() for x in resp.ret_values],
                "total_count": total_count,
            }
        )

        # TODO validate response data strictly, like below.
        # it'll fail because the data format will be different with EntryAttributeValueSerializer
        # serializer.is_valid(raise_exception=True)
        # return Response(serializer.validated_data)

        return Response(serializer.initial_data)


class AdvancedSearchChainAPI(generics.GenericAPIView):
    serializer_class = EntrySearchChainSerializer
    """
    NOTE For now, it's just copied from /api/v1/entry/search_chain.
    And the AttributeValue is missing from the response.
    """

    @extend_schema(
        request=EntrySearchChainSerializer,
        responses=EntryBaseSerializer(many=True),
    )
    def post(self, request: Request) -> Response:
        serializer = EntrySearchChainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            (_, ret_data) = serializer.search_entries(request.user)
        except ElasticsearchException:
            return Response(
                {
                    "reason": (
                        "Data overflow was happened. " "Please narrow down intermediate conditions"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        entries = Entry.objects.filter(id__in=[x["id"] for x in ret_data])

        return Response(EntryBaseSerializer(entries, many=True).data)


class AdvancedSearchResultAPI(generics.GenericAPIView):
    serializer_class = AdvancedSearchResultExportSerializer

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.validated_data)


@extend_schema(
    parameters=[
        OpenApiParameter("keyword", OpenApiTypes.STR, OpenApiParameter.QUERY),
    ],
)
class EntryReferralAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = EntryBaseSerializer
    pagination_class = EntryReferralPagination

    def get_queryset(self):
        entry_id = self.kwargs["pk"]
        keyword = self.request.query_params.get("keyword", None)

        entry = Entry.objects.filter(pk=entry_id).first()
        if not entry:
            return []

        ids = AttributeValue.objects.filter(
            Q(referral=entry, is_latest=True) | Q(referral=entry, parent_attrv__is_latest=True)
        ).values_list("parent_attr__parent_entry", flat=True)

        # if entity_name param exists, add schema name to reduce filter execution time
        query = Q(pk__in=ids, is_active=True)
        if keyword:
            query &= Q(name__iregex=r"%s" % keyword)

        return Entry.objects.filter(query).select_related("schema")


class EntryExportAPI(generics.GenericAPIView):
    serializer_class = EntryExportSerializer

    def post(self, request: Request, entity_id: int) -> Response:
        if not Entity.objects.filter(id=entity_id).exists():
            return Response(
                "Failed to get entity of specified id", status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                "Parameters in post body is invalid", status=status.HTTP_400_BAD_REQUEST
            )

        job_params = ExportTaskParams(
            export_format=serializer.validated_data["format"], target_id=entity_id
        )

        # check whether same job is sent
        job_status_not_finished = [JobStatus.PREPARING, JobStatus.PROCESSING]
        if (
            Job.get_job_with_params(request.user, job_params.dict())
            .filter(status__in=job_status_not_finished)
            .exists()
        ):
            return Response(
                "Same export processing is under execution", status=status.HTTP_400_BAD_REQUEST
            )

        entity = Entity.objects.get(id=entity_id)
        if not request.user.has_permission(entity, ACLType.Readable):
            return Response(
                'Permission denied to _value "%s"' % entity.name, status=status.HTTP_400_BAD_REQUEST
            )

        # create a job to export search result and run it
        job = Job.new_export_v2(
            request.user,
            **{
                "text": "entry_%s.%s" % (entity.name, str(job_params.export_format)),
                "target": entity,
                "params": job_params.dict(),
            },
        )
        job.run()

        return Response(
            {"result": "Succeed in registering export processing. " + "Please check Job list."},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    parameters=[
        OpenApiParameter("keyword", OpenApiTypes.STR, OpenApiParameter.QUERY),
    ],
)
class EntryAttrReferralsAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = GetEntryAttrReferralSerializer

    def get_queryset(self):
        attr_id = self.kwargs["attr_id"]
        keyword = self.request.query_params.get("keyword", None)

        attr = Attribute.objects.filter(id=attr_id).first()
        if attr:
            entity_attr = attr.schema
        else:
            entity_attr = EntityAttr.objects.filter(id=attr_id).first()
        if not entity_attr:
            raise NotFound(f"not found matched attribute or entity attr: {attr_id}")

        conditions = {"is_active": True}
        if keyword:
            conditions["name__icontains"] = keyword

        # TODO support natural sort?
        if entity_attr.type & AttrType.OBJECT:
            return Entry.objects.filter(
                **conditions, schema__in=entity_attr.referral.all()
            ).order_by("name")[0 : CONFIG.MAX_LIST_REFERRALS]
        elif entity_attr.type & AttrType.GROUP:
            return Group.objects.filter(**conditions).order_by("name")[
                0 : CONFIG.MAX_LIST_REFERRALS
            ]
        elif entity_attr.type & AttrType.ROLE:
            return Role.objects.filter(**conditions).order_by("name")[0 : CONFIG.MAX_LIST_REFERRALS]
        else:
            raise IncorrectTypeError(f"unsupported attr type: {entity_attr.type}")


@extend_schema(
    parameters=[
        OpenApiParameter("force", OpenApiTypes.BOOL, OpenApiParameter.QUERY, default=False),
    ],
)
class EntryImportAPI(generics.GenericAPIView):
    parser_classes = [YAMLParser]
    serializer_class = serializers.Serializer

    def get_queryset(self):
        import_data = self.request.data
        entity_names = [d["entity"] for d in import_data]
        return Entity.objects.filter(name__in=entity_names, is_active=True)

    def post(self, request: Request) -> Response:
        import_datas = request.data
        user: User = request.user
        serializer = EntryImportSerializer(data=import_datas)
        serializer.is_valid(raise_exception=True)
        entities = self.get_queryset()

        # limit import job to deny accidental frequent import for same entity
        if request.query_params.get("force", "") not in ["true", "True"]:
            valid_statuses: list[JobStatus] = [
                JobStatus.PREPARING,
                JobStatus.PROCESSING,
                JobStatus.DONE,
            ]
            yesterday = datetime.now() - timedelta(days=1)
            if Job.objects.filter(
                status__in=valid_statuses,
                operation=JobOperation.IMPORT_ENTRY_V2,
                target__in=entities,
                created_at__gte=yesterday,
            ).exists():
                raise FrequentImportError("Import job for each entity can apply once a day.")

        job_ids: list[int] = []
        error_list: list[str] = []
        for import_data in import_datas:
            entity: Entity | None = next(
                (e for e in entities if e.name == import_data["entity"]), None
            )
            if not entity:
                error_list.append("%s: Entity does not exists." % import_data["entity"])
                continue

            if not user.has_permission(entity, ACLType.Writable):
                error_list.append("%s: Entity is permission denied." % import_data["entity"])
                continue

            job = Job.new_import_v2(
                user, entity, text="Preparing to import data", params=import_data
            )
            job.run()
            job_ids.append(job.id)

        return Response(
            {"result": {"job_ids": job_ids, "error": error_list}}, status=status.HTTP_200_OK
        )


class EntryAttributeValueRestoreAPI(generics.UpdateAPIView):
    queryset = AttributeValue.objects.all()
    serializer_class = EntryAttributeValueRestoreSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(
    parameters=[
        OpenApiParameter(
            "ids", {"type": "array", "items": {"type": "number"}}, OpenApiParameter.QUERY
        ),
    ],
)
class EntryBulkDeleteAPI(generics.DestroyAPIView):
    def delete(self, request: Request, *args, **kwargs) -> Response:
        ids: list[str] = self.request.query_params.getlist("ids", [])
        if len(ids) == 0 or not all([id.isdecimal() for id in ids]):
            raise RequiredParameterError("some ids are invalid")

        entries = Entry.objects.filter(id__in=ids, is_active=True)
        if len(ids) != entries.count():
            raise NotFound("some specified entries don't exist")

        user: User = request.user
        if not all([user.has_permission(e, ACLType.Writable) for e in entries]):
            raise PermissionDenied("deleting some entries is not allowed")

        for entry in entries:
            job: Job = Job.new_delete_entry_v2(user, entry)
            job.run()

        return Response(status=status.HTTP_204_NO_CONTENT)
