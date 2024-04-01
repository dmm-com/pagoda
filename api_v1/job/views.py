from datetime import datetime, timedelta, timezone

from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from job.models import Job, JobOperation, JobStatus
from job.settings import CONFIG as JOB_CONFIG


class JobAPI(APIView):
    def get(self, request, format=None):
        """
        This returns only jobs that are created by the user who sends this request.
        """
        time_threashold = datetime.now(timezone.utc) - timedelta(seconds=JOB_CONFIG.RECENT_SECONDS)

        constant = {
            "status": {
                "processing": JobStatus.PROCESSING,
                "done": JobStatus.DONE,
                "error": JobStatus.ERROR,
                "timeout": JobStatus.TIMEOUT,
            },
            "operation": {
                "create": JobOperation.CREATE_ENTRY,
                "edit": JobOperation.EDIT_ENTRY,
                "delete": JobOperation.DELETE_ENTRY,
                "copy": JobOperation.COPY_ENTRY,
                "do_copy": JobOperation.DO_COPY_ENTRY,
                "import": JobOperation.IMPORT_ENTRY,
                "import_v2": JobOperation.IMPORT_ENTRY_V2,
                "export": JobOperation.EXPORT_ENTRY,
                "export_v2": JobOperation.EXPORT_ENTRY_V2,
                "export_search_result": JobOperation.EXPORT_SEARCH_RESULT,
                "export_search_result_v2": JobOperation.EXPORT_SEARCH_RESULT_V2,
                "restore": JobOperation.RESTORE_ENTRY,
                "create_entity": JobOperation.CREATE_ENTITY,
                "edit_entity": JobOperation.EDIT_ENTITY,
                "delete_entity": JobOperation.DELETE_ENTITY,
            },
        }

        query = Q(
            Q(user=request.user, created_at__gte=time_threashold),
            ~Q(operation__in=Job.HIDDEN_OPERATIONS),
        )
        jobs = [
            x.to_json()
            for x in Job.objects.filter(query).order_by("-created_at")[: JOB_CONFIG.MAX_LIST_NAV]
        ]

        return Response(
            {
                "result": jobs,
                "constant": constant,
            }
        )

    def delete(self, request, format=None):
        """
        This cancels a specified Job.
        """
        job_id = request.data.get("job_id", None)
        if not job_id:
            return Response("Parameter job_id is required", status=status.HTTP_400_BAD_REQUEST)

        job = Job.objects.filter(id=job_id).first()
        if not job:
            return Response(
                "Failed to find Job(id=%s)" % job_id, status=status.HTTP_400_BAD_REQUEST
            )

        if job.status == JobStatus.DONE:
            return Response("Target job has already been done")

        if job.operation not in Job.CANCELABLE_OPERATIONS:
            return Response("Target job cannot be canceled", status=status.HTTP_400_BAD_REQUEST)

        # update job.status to be canceled
        job.update(JobStatus.CANCELED)

        return Response("Success to cancel job")


class SpecificJobAPI(APIView):
    def post(self, request, job_id, format=None):
        job = Job.objects.filter(id=job_id).first()
        if not job:
            return Response(
                "Failed to find Job(id=%s)" % job_id, status=status.HTTP_400_BAD_REQUEST
            )

        # check job status before starting processing
        if job.status == JobStatus.DONE:
            return Response("Target job has already been done")
        elif job.status == JobStatus.PROCESSING:
            return Response("Target job is under processing", status=status.HTTP_400_BAD_REQUEST)

        # check job target status
        if not job.target.is_active:
            return Response(
                "Job target has already been deleted",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Run job on an Application node
        job.run(will_delay=False)

        return Response("Success to run command")


class SearchJob(APIView):
    def get(self, request):
        """
        This returns jobs that are matched to the specified conditions in spite of who makes.
        """

        def _update_query_by_get_param(query, query_key, get_param):
            param = request.GET.get(get_param)
            if param:
                return Q(query, **{query_key: param})
            else:
                return query

        query = _update_query_by_get_param(Q(), "operation", "operation")
        query = _update_query_by_get_param(query, "target__id", "target_id")

        if not query.children:
            return Response(
                "You have to specify (at least one) condition to search",
                status=status.HTTP_400_BAD_REQUEST,
            )

        jobs = Job.objects.filter(query).order_by("-created_at")
        if not jobs:
            return Response(
                "There is no job that is matched specified condition",
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"result": [x.to_json() for x in jobs]})
