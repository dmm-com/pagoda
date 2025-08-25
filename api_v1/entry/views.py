from datetime import datetime
from typing import List, Optional

import pytz
from django.conf import settings
from django.db.models import Q
from pydantic import BaseModel, Field, RootModel, ValidationError, field_validator
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from airone.exceptions import ElasticsearchException
from airone.lib.acl import ACLType
from airone.lib.elasticsearch import (
    AdvancedSearchResultRecord,
    AdvancedSearchResults,
    AttrHint,
)
from api_v1.entry.serializer import EntrySearchChainSerializer
from entity.models import Entity
from entry.models import Entry
from entry.services import AdvancedSearchService
from entry.settings import CONFIG as CONFIG_ENTRY


class EntrySearchChainAPIResponse(BaseModel):
    ret_count: int
    ret_values: List[AdvancedSearchResultRecord]


class EntrySearchAPIRequest(BaseModel):
    entities: list[int | str]
    entry_name: str = Field(default="", max_length=CONFIG_ENTRY.MAX_QUERY_SIZE)
    referral: str | None = None
    attrinfo: list = Field(default_factory=list)
    is_output_all: bool = True
    entry_limit: int = Field(default=CONFIG_ENTRY.MAX_LIST_ENTRIES, gt=0)

    @field_validator("entities")
    def validate_entities_not_empty(cls, v):
        if not v or len(v) < 1:
            raise ValueError("At least one entity is required")
        return v

    @field_validator("attrinfo")
    def validate_attrinfo_keyword_length(cls, v):
        for item in v:
            if isinstance(item, dict) and "keyword" in item and item["keyword"]:
                if len(item["keyword"]) > CONFIG_ENTRY.MAX_QUERY_SIZE:
                    raise ValueError("Keyword length exceeds maximum allowed size")
        return v


class EntrySearchAPIResponse(BaseModel):
    result: AdvancedSearchResults


class EntrySearchChainAPI(APIView):
    def post(self, request):
        serializer = EntrySearchChainSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        try:
            (_, ret_data) = serializer.search_entries(request.user)
        except ElasticsearchException:
            return Response(
                {
                    "reason": (
                        "Data overflow was happened. Please narrow down intermediate conditions"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if ret_data:
            # output all Attributes of returned Entries. This divides input entry names for
            # search processing into 100 pieces to prevent hung-up
            # while AdvancedSearchService.search_entries() because of big input data.
            result = {"ret_count": len(ret_data), "ret_values": []}
            for i in range(0, len(ret_data), 100):
                entry_info = AdvancedSearchService.search_entries(
                    request.user,
                    serializer.validated_data["entities"],
                    entry_name="|".join(["^%s$" % x["name"] for x in ret_data[i : i + 100]]),
                    is_output_all=True,
                )
                result["ret_values"].extend([x.model_dump() for x in entry_info.ret_values])
            return Response(
                EntrySearchChainAPIResponse(**result).model_dump(), status=status.HTTP_200_OK
            )

        else:
            return Response(
                EntrySearchChainAPIResponse(ret_count=0, ret_values=[]).model_dump(),
                status=status.HTTP_200_OK,
            )


class EntrySearchAPI(APIView):
    def post(self, request, format=None):
        if not isinstance(request.data, dict):
            return Response(
                "parameter must be in dictionary format", status=status.HTTP_400_BAD_REQUEST
            )

        try:
            params = EntrySearchAPIRequest.model_validate(request.data)
        except ValidationError as e:
            errors = e.errors()
            for error in errors:
                if error.get("loc"):
                    match error.get("loc")[0]:
                        case "entities":
                            return Response("The entities parameters are required", status=400)
                        case "entry_name":
                            return Response("Sending parameter is too large", status=400)
                        case "attrinfo":
                            return Response("Sending parameter is too large", status=400)
                        case "entry_limit" if error.get("type") == "value_error.number.not_gt":
                            return Response(
                                "Entry limit must be greater than 0",
                                status=status.HTTP_400_BAD_REQUEST,
                            )
            return Response(
                "The type of parameter is incorrect", status=status.HTTP_400_BAD_REQUEST
            )

        try:
            hint_attrs = [
                AttrHint(
                    name=x.get("name"),
                    keyword=x.get("keyword"),
                    filter_key=x.get("filter_key"),
                    exact_match=x.get("exact_match"),
                )
                for x in params.attrinfo
            ]
        except (TypeError, ValidationError, AttributeError):
            return Response(
                "The type of parameter 'attrinfo' is incorrect",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # check entities params
        hint_entity_ids = []
        for hint_entity in params.entities:
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

        resp = AdvancedSearchService.search_entries(
            request.user,
            hint_entity_ids,
            hint_attrs,
            params.entry_limit,
            params.entry_name,
            params.referral,
            params.is_output_all,
        )

        return Response(EntrySearchAPIResponse(result=resp).model_dump(), status=status.HTTP_200_OK)


class EntryReferredResponse(BaseModel):
    class Entity(BaseModel):
        id: Optional[int] = None
        name: Optional[str] = None

    class ReferralEntry(BaseModel):
        id: int
        name: str
        entity: Optional["EntryReferredResponse.Entity"] = None

    class EntryReferred(BaseModel):
        id: int
        entity: "EntryReferredResponse.Entity"
        referral: List["EntryReferredResponse.ReferralEntry"]

    result: List[EntryReferred]


class EntryReferredAPI(APIView):
    def get(self, request: Request) -> Response:
        # set each request parameters to description variables
        param_entity: str | None = request.query_params.get("entity")
        param_entry: str | None = request.query_params.get("entry")
        param_target_entity: str | None = request.query_params.get("target_entity")
        param_quiet: str | None = request.query_params.get("quiet")

        # validate input parameter
        if not param_entry:
            return Response(
                {"result": 'Parameter "entry" is mandatory'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # declare query to send DB according to input parameters
        query = Q(name=param_entry, is_active=True)
        if param_entity:
            query &= Q(schema__name=param_entity)

        filter_entities = [param_target_entity] if param_target_entity else []

        entries_data = [
            EntryReferredResponse.EntryReferred(
                id=entry.id,
                entity=EntryReferredResponse.Entity(id=entry.schema.id, name=entry.schema.name),
                referral=[
                    EntryReferredResponse.ReferralEntry(
                        id=referred_entry.id,
                        name=referred_entry.name,
                        entity=EntryReferredResponse.Entity()
                        if param_quiet
                        else EntryReferredResponse.Entity(
                            id=referred_entry.schema.id, name=referred_entry.schema.name
                        ),
                    )
                    for referred_entry in entry.get_referred_objects(
                        filter_entities=filter_entities
                    )
                ],
            )
            for entry in Entry.objects.filter(query)
        ]

        return Response(EntryReferredResponse(result=entries_data).model_dump(exclude_none=True))


class UpdateHistoryResponse(RootModel[List["UpdateHistoryResponse.ResponseItem"]]):
    class Entity(BaseModel):
        id: int
        name: str

    class Entry(BaseModel):
        id: int
        name: str

    class AttributeHistory(BaseModel):
        value: object
        updated_at: datetime
        updated_username: str
        updated_userid: int

    class Attribute(BaseModel):
        id: int
        name: str
        history: List["UpdateHistoryResponse.AttributeHistory"]

    class ResponseItem(BaseModel):
        entity: "UpdateHistoryResponse.Entity"
        entry: "UpdateHistoryResponse.Entry"
        attribute: "UpdateHistoryResponse.Attribute"


class UpdateHistory(APIView):
    def get(self, request: Request) -> Response:
        # validate whether mandatory parameters are specified
        p_attr = request.GET.get("attribute")
        if not p_attr:
            return Response("'attribute' parameter is required", status=status.HTTP_400_BAD_REQUEST)

        # both entry and entry_id parameters accept str and connma separated array
        p_entry = request.GET.get("entry", "")
        p_entry_id = request.GET.get("entry_id", "")
        if not (p_entry or p_entry_id):
            return Response(
                "Either 'entries' or 'entry_ids' parameter is required",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set variables that describe timerange to filter the result of AttributeValue with them.
        older_than = datetime.now(pytz.timezone(settings.TIME_ZONE))
        p_older_than = request.GET.get("older_than")
        if p_older_than:
            try:
                older_than = datetime.strptime(p_older_than, CONFIG_ENTRY.TIME_FORMAT).replace(
                    tzinfo=pytz.timezone(settings.TIME_ZONE)
                )
            except ValueError:
                return Response(
                    ("The older_than parameter accepts for following format 'YYYY-MM-DDTHH:MM:SS'"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # The initial datetime(1900/01/01 00:00:00) represents good enough past time to compare
        # with the created time of AttributeValue. We could handle minimum time by using
        # 'datetime.MIN', but some library and service couldn't deal with this time.
        # (c.f. https://dev.mysql.com/doc/refman/5.7/en/datetime.html)
        newer_than = datetime(1900, 1, 1, tzinfo=pytz.timezone(settings.TIME_ZONE))
        p_newer_than = request.GET.get("newer_than")
        if p_newer_than:
            try:
                newer_than = datetime.strptime(p_newer_than, CONFIG_ENTRY.TIME_FORMAT).replace(
                    tzinfo=pytz.timezone(settings.TIME_ZONE)
                )
            except ValueError:
                return Response(
                    ("The newer_than parameter accepts for following format 'YYYY-MM-DDTHH:MM:SS'"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # get target entries to get update history
        q_base = Q(is_active=True)
        p_entity = request.GET.get("entity")
        if p_entity:
            q_base &= Q(schema__name=p_entity)

        target_entries = Entry.objects.filter(
            q_base,
            (
                Q(name__in=p_entry.split(","))
                | Q(id__in=[int(x) for x in p_entry_id.split(",") if x])
            ),
        )
        if not target_entries.exists():
            return Response(
                "There is no entry with which matches specified parameters",
                status=status.HTTP_400_BAD_REQUEST,
            )

        results: List[UpdateHistoryResponse.ResponseItem] = []
        for entry in target_entries:
            attr = entry.attrs.filter(schema__name=p_attr, is_active=True).first()
            if not attr:
                return Response(
                    "There is no attribute(%s) in entry(%s)" % (p_attr, entry.name),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            history_items: List[UpdateHistoryResponse.AttributeHistory] = []
            for attrv in attr.values.filter(
                created_time__gt=newer_than, created_time__lt=older_than
            ).order_by("-created_time")[: CONFIG_ENTRY.MAX_HISTORY_COUNT]:
                history_items.append(
                    UpdateHistoryResponse.AttributeHistory(
                        value=attrv.get_value(with_metainfo=True)["value"],
                        updated_at=attrv.created_time,
                        updated_username=attrv.created_user.username,
                        updated_userid=attrv.created_user.id,
                    )
                )

            results.append(
                UpdateHistoryResponse.ResponseItem(
                    entity=UpdateHistoryResponse.Entity(
                        id=entry.schema.id,
                        name=entry.schema.name,
                    ),
                    entry=UpdateHistoryResponse.Entry(
                        id=entry.id,
                        name=entry.name,
                    ),
                    attribute=UpdateHistoryResponse.Attribute(
                        id=attr.id,
                        name=attr.schema.name,
                        history=history_items,
                    ),
                )
            )

        return Response(UpdateHistoryResponse(results).model_dump(mode="json"))
