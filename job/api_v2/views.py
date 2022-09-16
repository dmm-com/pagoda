from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from job.api_v2.serializers import JobSerializers
from job.models import Job, JobOperation


class JobAPI(viewsets.ModelViewSet):
    serializer_class = JobSerializers

    def get_queryset(self):
        return Job.objects.filter(user=self.request.user)


@extend_schema(
    parameters=[
        OpenApiParameter("created_after", OpenApiTypes.DATETIME, OpenApiParameter.QUERY),
    ],
)
class JobListAPI(viewsets.ModelViewSet):
    serializer_class = JobSerializers
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        user = self.request.user
        created_after = self.request.query_params.get("created_after", None)

        export_operations = [
            JobOperation.EXPORT_ENTRY.value,
            JobOperation.EXPORT_SEARCH_RESULT.value,
        ]
        query = Q(
            Q(user=user),
            ~Q(operation__in=Job.HIDDEN_OPERATIONS),
            Q(
                Q(operation__in=export_operations)
                | Q(
                    ~Q(operation__in=export_operations),
                    target__isnull=False,
                    target__is_active=True,
                )
                | Q(operation=JobOperation.DELETE_ENTITY.value, target__isnull=False)
                | Q(operation=JobOperation.DELETE_ENTRY.value, target__isnull=False)
            ),
        )

        if created_after:
            query &= Q(created_at__gte=created_after)

        return Job.objects.filter(query).order_by("-created_at")
