from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from entry.api_v2.serializers import GetEntrySerializer
from entry.api_v2.serializers import GetEntrySimpleSerializer
from entry.api_v2.serializers import GetEntryWithAttrSerializer
from entry.models import AttributeValue, Entry


class entryAPI(viewsets.ReadOnlyModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = GetEntrySerializer
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['is_active']
    ordering_fields = ['name']
    search_fields = ['name']

    def get_queryset(self):
        return self.queryset.filter(schema__id=self.kwargs.get('entity_id'))


class entryWithAttrAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = GetEntryWithAttrSerializer
    ordering_fields = ['name']

    def get_queryset(self):
        is_active = self.request.query_params.get('is_active', 'true').lower() == 'true'
        return Entry.objects.filter(is_active=is_active)


class searchAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = GetEntrySimpleSerializer

    def get_queryset(self):
        queryset = []
        query = self.request.query_params.get('query', None)

        if not query:
            return queryset

        name_results = list(Entry.objects.filter(name__iregex=r'%s' % query,
                                                 is_active=True).order_by('name'))
        value_results = [x.parent_attr.parent_entry for x in AttributeValue.objects.select_related(
                         'parent_attr__parent_entry').filter(Q(value__iregex=r'%s' % query),
                         Q(is_latest=True) | Q(parent_attrv__is_latest=True),
                         Q(parent_attr__parent_entry__is_active=True)).order_by(
                         'parent_attr__parent_entry__name')]
        ref_results = [x.parent_attr.parent_entry for x in AttributeValue.objects.select_related(
                       'parent_attr__parent_entry', 'referral').filter(
                       Q(referral__is_active=True), Q(referral__name__iregex=r'%s' % query),
                       Q(is_latest=True) | Q(parent_attrv__is_latest=True),
                       Q(parent_attr__parent_entry__is_active=True)).order_by(
                       'parent_attr__parent_entry__name')]
        results = name_results + value_results + ref_results
        queryset = sorted(set(results), key=results.index)

        return queryset
