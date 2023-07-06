import re

from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, serializers, status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

import custom_view
from airone.lib.acl import ACLType
from airone.lib.drf import (
    DuplicatedObjectExistsError,
    IncorrectTypeError,
    ObjectNotExistsError,
    YAMLParser,
)
from airone.lib.types import AttrTypeValue
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
from group.models import Group
from job.models import Job
from role.models import Role
from user.models import User


class EntryPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
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
            "update": EntryUpdateSerializer,
            "copy": EntryCopySerializer,
            "list": EntryHistoryAttributeValueSerializer,
        }
        return serializer.get(self.action, EntryBaseSerializer)

    def destroy(self, request, pk):
        entry: Entry = self.get_object()
        if not entry.is_active:
            raise ObjectNotExistsError("specified entry has already been deleted")

        user: User = request.user

        if custom_view.is_custom("before_delete_entry_v2", entry.schema.name):
            custom_view.call_custom("before_delete_entry_v2", entry.schema.name, user, entry)

        # register operation History for deleting entry
        user.seth_entry_del(entry)

        # delete entry
        entry.delete(deleted_user=user)

        if custom_view.is_custom("after_delete_entry_v2", entry.schema.name):
            custom_view.call_custom("after_delete_entry_v2", entry.schema.name, user, entry)

        # Send notification to the webhook URL
        job_notify: Job = Job.new_notify_delete_entry(user, entry)
        job_notify.run()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def restore(self, request, pk):
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

    def copy(self, request, pk):
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
    def list(self, request, pk):
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

        return super(EntryAPI, self).list(request, pk)


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
    def post(self, request, format=None):
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

        resp = Entry.search_entries(
            request.user,
            hint_entity_ids,
            hint_attrs,
            entry_limit,
            hint_entry_name,
            hint_referral,
            is_output_all,
            offset=entry_offset,
        )

        # convert field values to fit entry retrieve API data type, as a workaround.
        # FIXME should be replaced with DRF serializer etc
        for entry in resp["ret_values"]:
            for name, attr in entry["attrs"].items():

                def _get_typed_value(type: int) -> str:
                    if type & AttrTypeValue["array"]:
                        if type & AttrTypeValue["string"]:
                            return "as_array_string"
                        elif type & AttrTypeValue["named"]:
                            return "as_array_named_object"
                        elif type & AttrTypeValue["object"]:
                            return "as_array_object"
                        elif type & AttrTypeValue["group"]:
                            return "as_array_group"
                        elif type & AttrTypeValue["role"]:
                            return "as_array_role"
                    elif type & AttrTypeValue["string"] or type & AttrTypeValue["text"]:
                        return "as_string"
                    elif type & AttrTypeValue["named"]:
                        return "as_named_object"
                    elif type & AttrTypeValue["object"]:
                        return "as_object"
                    elif type & AttrTypeValue["boolean"]:
                        return "as_boolean"
                    elif type & AttrTypeValue["date"]:
                        return "as_string"
                    elif type & AttrTypeValue["group"]:
                        return "as_group"
                    elif type & AttrTypeValue["role"]:
                        return "as_role"
                    raise IncorrectTypeError(f"unexpected type: {type}")

                entry["attrs"][name] = {
                    "is_readable": attr["is_readable"],
                    "type": attr["type"],
                    "value": {
                        _get_typed_value(attr["type"]): attr.get("value", ""),
                    },
                }

                # "asString" is a string type and does not allow None
                if (
                    _get_typed_value(attr["type"]) == "as_string"
                    and entry["attrs"][name]["value"]["as_string"] is None
                ):
                    entry["attrs"][name]["value"]["as_string"] = ""

        serializer = AdvancedSearchResultSerializer(
            data={"count": resp["ret_count"], "values": resp["ret_values"]}
        )

        # TODO validate response data strictly, like below.
        # it'll fail because the data format will be different with EntryAttributeValueSerializer
        # serializer.is_valid(raise_exception=True)
        # return Response(serializer.validated_data)

        return Response(serializer.initial_data)


class AdvancedSearchResultAPI(generics.GenericAPIView):
    serializer_class = AdvancedSearchResultExportSerializer

    def post(self, request):
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

    def post(self, request, entity_id: int):
        if not Entity.objects.filter(id=entity_id).exists():
            return Response(
                "Failed to get entity of specified id", status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                "Parameters in post body is invalid", status=status.HTTP_400_BAD_REQUEST
            )

        job_params = {
            "export_format": serializer.validated_data["format"],
            "target_id": entity_id,
        }

        # check whether same job is sent
        job_status_not_finished = [Job.STATUS["PREPARING"], Job.STATUS["PROCESSING"]]
        if (
            Job.get_job_with_params(request.user, job_params)
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
                "text": "entry_%s.%s" % (entity.name, job_params["export_format"]),
                "target": entity,
                "params": job_params,
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
        if entity_attr.type & AttrTypeValue["object"]:
            return Entry.objects.filter(
                **conditions, schema__in=entity_attr.referral.all()
            ).order_by("name")[0 : CONFIG.MAX_LIST_REFERRALS]
        elif entity_attr.type & AttrTypeValue["group"]:
            return Group.objects.filter(**conditions).order_by("name")[
                0 : CONFIG.MAX_LIST_REFERRALS
            ]
        elif entity_attr.type & AttrTypeValue["role"]:
            return Role.objects.filter(**conditions).order_by("name")[0 : CONFIG.MAX_LIST_REFERRALS]
        else:
            raise IncorrectTypeError(f"unsupported attr type: {entity_attr.type}")


class EntryImportAPI(generics.GenericAPIView):
    parser_classes = [YAMLParser]
    serializer_class = serializers.Serializer

    def post(self, request):
        import_datas = request.data
        user: User = request.user
        serializer = EntryImportSerializer(data=import_datas)
        serializer.is_valid(raise_exception=True)

        job_ids = []
        error_list = []
        for import_data in import_datas:
            entity = Entity.objects.filter(name=import_data["entity"], is_active=True).first()
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
