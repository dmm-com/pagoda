from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.http import Http404

from airone.lib.acl import ACLType
from entry.api_v2.serializers import GetEntrySerializer
from entry.api_v2.serializers import GetEntrySimpleSerializer
from entry.api_v2.serializers import GetEntryWithAttrSerializer
from entry.models import AttributeValue, Entry
from entity.models import Entity
from user.models import User


class EntryPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == "list":
            user = User.objects.get(id=request.user.id)
            entity = Entity.objects.filter(id=view.kwargs.get("entity_id")).first()

            if not entity:
                raise Http404

            if not user.has_permission(entity, ACLType.Readable):
                return False

        return True

    def has_object_permission(self, request, view, obj):
        user = User.objects.get(id=request.user.id)

        if not user.has_permission(obj, ACLType.Readable):
            return False

        return True


class entryAPI(viewsets.ReadOnlyModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = GetEntrySerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated & EntryPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = ["is_active"]
    ordering_fields = ["name"]
    search_fields = ["name"]

    def get_queryset(self):
        return self.queryset.filter(schema__id=self.kwargs.get("entity_id"))


class entryWithAttrAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = GetEntryWithAttrSerializer
    permission_classes = [IsAuthenticated & EntryPermission]
    ordering_fields = ["name"]

    def get_queryset(self):
        is_active = self.request.query_params.get("is_active", "true").lower() == "true"
        return Entry.objects.filter(is_active=is_active).select_related("schema")


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
