from django.db.models import Q

# libraries of AirOne
from rest_framework import viewsets

# related models in AirOne
from job.api_v2.serializers import JobSerializer
from job.models import Job, JobOperation

# configuration of this app
from job.settings import CONFIG


class JobAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = JobSerializer

    def get_queryset(self):
        user = self.request.user

        limitation = CONFIG.MAX_LIST_VIEW
        if self.request.query_params.get('nolimit', None):
            limitation = None

        export_operations = [
            JobOperation.EXPORT_ENTRY.value,
            JobOperation.EXPORT_SEARCH_RESULT.value,
        ]
        query = Q(Q(user=user), ~Q(operation__in=Job.HIDDEN_OPERATIONS), Q(
            Q(operation__in=export_operations, target__isnull=False, target__is_active=True)|
            Q(~Q(operation__in=export_operations), target__isnull=False) |
            Q(operation=JobOperation.DELETE_ENTITY.value, target__isnull=False) |
            Q(operation=JobOperation.DELETE_ENTITY.value, target__isnull=False)
        ))

        return Job.objects.filter(query).order_by('-created_at')[:limitation]
