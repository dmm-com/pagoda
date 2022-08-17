from datetime import datetime, timezone

from django.db.models import Q
from django.http import JsonResponse
from rest_framework import viewsets

from airone.lib.http import http_get
from job.api_v2.serializers import JobSerializers
from job.models import Job, JobOperation
from job.settings import CONFIG


class JobAPI(viewsets.ModelViewSet):
    serializer_class = JobSerializers

    def get_queryset(self):
        return Job.objects.filter(user=self.request.user)


@http_get
def list_jobs(request):
    limitation = CONFIG.MAX_LIST_VIEW
    if request.GET.get("nolimit", None):
        limitation = None

    export_operations = [
        JobOperation.EXPORT_ENTRY.value,
        JobOperation.EXPORT_SEARCH_RESULT.value,
    ]

    query = Q(Q(user=request.user), ~Q(operation__in=Job.HIDDEN_OPERATIONS))

    jobs = [
        x
        for x in Job.objects.filter(query).order_by("-created_at")[:limitation]
        if (
            x.operation in export_operations
            or (x.operation not in export_operations and x.target and x.target.is_active)
            or (x.operation is JobOperation.DELETE_ENTITY.value and x.target)
            or (x.operation is JobOperation.DELETE_ENTRY.value and x.target)
        )
    ]

    return JsonResponse(
        [
            {
                "id": x.id,
                "target": {
                    "id": x.target.id,
                    "name": x.target.name,
                }
                if x.target
                else {},
                "text": x.text,
                "status": x.status,
                "operation": x.operation,
                "created_at": x.created_at,
                "passed_time": (x.updated_at - x.created_at).seconds
                if x.is_finished()
                else (datetime.now(timezone.utc) - x.created_at).seconds,
            }
            for x in jobs
        ],
        safe=False,
    )
