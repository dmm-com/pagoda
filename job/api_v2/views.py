from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, serializers, status, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from job.api_v2.serializers import JobSerializers
from job.models import Job, JobOperation


class JobAPI(viewsets.ModelViewSet):
    serializer_class = JobSerializers

    def get_queryset(self):
        return Job.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        job: Job = self.get_object()

        if job.status == Job.STATUS["DONE"]:
            return Response("Target job has already been done", status=status.HTTP_400_BAD_REQUEST)
        if job.operation not in Job.CANCELABLE_OPERATIONS:
            return Response("Target job cannot be canceled", status=status.HTTP_400_BAD_REQUEST)

        # update job.status to be canceled
        job.update(Job.STATUS["CANCELED"])

        return Response(status=status.HTTP_204_NO_CONTENT)


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


class JobRerunAPI(generics.UpdateAPIView):
    serializer_class = serializers.Serializer

    def get_queryset(self):
        return Job.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        return Response(
            "Unsupported. use PATCH alternatively", status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def patch(self, request, *args, **kwargs):
        job: Job = self.get_object()

        # check job status before starting processing
        if job.status == Job.STATUS["DONE"]:
            return Response("Target job has already been done")
        elif job.status == Job.STATUS["PROCESSING"]:
            return Response("Target job is under processing", status=status.HTTP_400_BAD_REQUEST)

        # check job target status
        if not job.target.is_active:
            return Response(
                "Job target has already been deleted", status=status.HTTP_400_BAD_REQUEST
            )

        # Run job on an Application node
        job.run(will_delay=False)

        return Response("Success to run command")
