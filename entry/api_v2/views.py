# from rest_framework import viewsets, filters
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
# from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

import custom_view
from airone.lib.acl import ACLType
from entry.api_v2.serializers import GetEntrySimpleSerializer
from entry.api_v2.serializers import EntryBaseSerializer, EntryRetrieveSerializer
from entry.api_v2.serializers import EntryCreateSerializer, EntryUpdateSerializer
from entry.models import AttributeValue, Entry
from job.models import Job
from user.models import User


class EntryPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = User.objects.get(id=request.user.id)
        permisson = {
            'retrieve': ACLType.Readable,
            'update': ACLType.Writable,
            'destroy': ACLType.Writable,
        }

        if not user.has_permission(obj, permisson.get(view.action)):
            return False

        return True


class EntryAPI(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated & EntryPermission]

    def get_serializer_class(self):
        serializer = {
            'retrieve': EntryRetrieveSerializer,
            'update': EntryUpdateSerializer,
            'create': EntryCreateSerializer,
        }
        return serializer.get(self.action, EntryBaseSerializer)

    def perform_destroy(self, entry: Entry):
        if not entry.is_active:
            raise ValidationError("specified entry has already been deleted")

        user = User.objects.get(id=self.request.user.id)

        if custom_view.is_custom("before_delete_entry", entry.schema.name):
            custom_view.call_custom("before_delete_entry", entry.schema.name, user, entry)

        # register operation History for deleting entry
        user.seth_entry_del(entry)

        # delete entry
        entry.delete()

        if custom_view.is_custom("after_delete_entry", entry.schema.name):
            custom_view.call_custom("after_delete_entry", entry.schema.name, user, entry)

        # Send notification to the webhook URL
        job_notify = Job.new_notify_delete_entry(user, entry)
        job_notify.run()


'''
    permission_classes = [IsAuthenticated & EntryPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['is_active']
    ordering_fields = ['name']
    search_fields = ['name']
'''


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
