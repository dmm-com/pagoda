import re

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

import custom_view
from airone.lib.acl import ACLType
from entry.api_v2.pagination import EntryReferralPagination
from entry.api_v2.serializers import GetEntrySimpleSerializer
from entry.api_v2.serializers import EntryBaseSerializer
from entry.api_v2.serializers import EntryRetrieveSerializer
from entry.api_v2.serializers import EntryUpdateSerializer
from entry.models import AttributeValue, Entry
from job.models import Job
from user.models import User


class EntryPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user: User = request.user
        permisson = {
            "retrieve": ACLType.Readable,
            "update": ACLType.Writable,
            "destroy": ACLType.Full,
            "restore": ACLType.Full,
        }

        if not user.has_permission(obj, permisson.get(view.action)):
            return False

        return True


class EntryAPI(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    permission_classes = [IsAuthenticated & EntryPermission]

    def get_serializer_class(self):
        serializer = {
            "retrieve": EntryRetrieveSerializer,
            "update": EntryUpdateSerializer,
        }
        return serializer.get(self.action, EntryBaseSerializer)

    def destroy(self, request, pk):
        entry: Entry = self.get_object()
        if not entry.is_active:
            raise ValidationError("specified entry has already been deleted")

        user: User = request.user

        if custom_view.is_custom("before_delete_entry", entry.schema.name):
            custom_view.call_custom("before_delete_entry", entry.schema.name, user, entry)

        # register operation History for deleting entry
        user.seth_entry_del(entry)

        # delete entry
        entry.delete()

        if custom_view.is_custom("after_delete_entry", entry.schema.name):
            custom_view.call_custom("after_delete_entry", entry.schema.name, user, entry)

        # Send notification to the webhook URL
        job_notify: Job = Job.new_notify_delete_entry(user, entry)
        job_notify.run()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def restore(self, request, pk):
        entry: Entry = self.get_object()

        if entry.is_active:
            raise ValidationError("specified entry has not deleted")

        # checks that a same name entry corresponding to the entity is existed, or not.
        if Entry.objects.filter(
            schema=entry.schema, name=re.sub(r"_deleted_[0-9_]*$", "", entry.name), is_active=True
        ).exists():
            raise ValidationError("specified entry has already exist other")

        user: User = request.user

        if custom_view.is_custom("before_restore_entry", entry.schema.name):
            custom_view.call_custom("before_restore_entry", entry.schema.name, user, entry)

        entry.set_status(Entry.STATUS_CREATING)

        # restore entry
        entry.restore()

        if custom_view.is_custom("after_restore_entry", entry.schema.name):
            custom_view.call_custom("after_restore_entry", entry.schema.name, user, entry)

        # remove status flag which is set before calling this
        entry.del_status(Entry.STATUS_CREATING)

        # Send notification to the webhook URL
        job_notify_event = Job.new_notify_create_entry(user, entry)
        job_notify_event.run()

        return Response(status=status.HTTP_201_CREATED)


class searchAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = GetEntrySimpleSerializer

    def get_queryset(self):
        queryset = []
        query = self.request.query_params.get("query", None)

        if not query:
            return queryset

        name_results = list(
            Entry.objects.filter(name__iregex=r"%s" % query, is_active=True).order_by("name")
        )
        value_results = [
            x.parent_attr.parent_entry
            for x in AttributeValue.objects.select_related("parent_attr__parent_entry")
            .filter(
                Q(value__iregex=r"%s" % query),
                Q(is_latest=True) | Q(parent_attrv__is_latest=True),
                Q(parent_attr__parent_entry__is_active=True),
            )
            .order_by("parent_attr__parent_entry__name")
        ]
        ref_results = [
            x.parent_attr.parent_entry
            for x in AttributeValue.objects.select_related("parent_attr__parent_entry", "referral")
            .filter(
                Q(referral__is_active=True),
                Q(referral__name__iregex=r"%s" % query),
                Q(is_latest=True) | Q(parent_attrv__is_latest=True),
                Q(parent_attr__parent_entry__is_active=True),
            )
            .order_by("parent_attr__parent_entry__name")
        ]
        results = name_results + value_results + ref_results
        queryset = sorted(set(results), key=results.index)

        return queryset


@extend_schema(
    parameters=[
        OpenApiParameter("keyword", OpenApiTypes.STR, OpenApiParameter.QUERY),
    ],
)
class EntryReferralAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = GetEntrySimpleSerializer
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

        return Entry.objects.filter(query)
