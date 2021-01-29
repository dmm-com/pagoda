from datetime import datetime, timedelta, timezone
from django.db.models import Q

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from job.models import Job, JobOperation
from job.settings import CONFIG as JOB_CONFIG
from user.models import User

from airone.lib.profile import airone_profile
from api_v1.auth import AironeTokenAuth


class JobAPI(APIView):
    authentication_classes = (AironeTokenAuth, BasicAuthentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    @airone_profile
    def get(self, request, format=None):
        """
        This returns only jobs that are created by the user who sends this request.
        """

        user = User.objects.get(id=request.user.id)
        time_threashold = (datetime.now(timezone.utc) -
                           timedelta(seconds=JOB_CONFIG.RECENT_SECONDS))

        constant = {
            'status': {
                'processing': Job.STATUS['PROCESSING'],
                'done': Job.STATUS['DONE'],
                'error': Job.STATUS['ERROR'],
                'timeout': Job.STATUS['TIMEOUT'],
            },
            'operation': {
                'create': JobOperation.CREATE_ENTRY.value,
                'edit': JobOperation.EDIT_ENTRY.value,
                'delete': JobOperation.DELETE_ENTRY.value,
                'copy': JobOperation.COPY_ENTRY.value,
                'import': JobOperation.IMPORT_ENTRY.value,
                'export': JobOperation.EXPORT_ENTRY.value,
                'export_search_result': JobOperation.EXPORT_SEARCH_RESULT.value,
                'restore': JobOperation.RESTORE_ENTRY.value,
            }
        }

        query = Q(
            Q(user=user, created_at__gte=time_threashold),
            ~Q(operation__in=Job.HIDDEN_OPERATIONS)
        )
        jobs = [
            x.to_json() for x in Job.objects.filter(query).order_by('-created_at')
            [:JOB_CONFIG.MAX_LIST_NAV]]

        return Response({
            'result': jobs,
            'constant': constant,
        }, content_type='application/json; charset=UTF-8')

    @airone_profile
    def delete(self, request, format=None):
        """
        This cancels a specified Job.
        """
        job_id = request.data.get('job_id', None)
        if not job_id:
            return Response('Parameter job_id is required', status=status.HTTP_400_BAD_REQUEST)

        job = Job.objects.filter(id=job_id).first()
        if not job:
            return Response('Failed to find Job(id=%s)' % job_id,
                            status=status.HTTP_400_BAD_REQUEST)

        if job.status == Job.STATUS['DONE']:
            return Response('Target job has already been done')

        # update job.status to be canceled
        job.update(Job.STATUS['CANCELED'])

        return Response('Success to cancel job')


class SpecificJobAPI(APIView):
    authentication_classes = (AironeTokenAuth, BasicAuthentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    @airone_profile
    def post(self, request, job_id, format=None):
        job = Job.objects.filter(id=job_id).first()
        if not job:
            return Response('Failed to find Job(id=%s)' % job_id,
                            status=status.HTTP_400_BAD_REQUEST)

        # check job status before starting processing
        if job.status == Job.STATUS['DONE']:
            return Response('Target job has already been done')
        elif job.status == Job.STATUS['PROCESSING']:
            return Response('Target job is under processing', status=status.HTTP_400_BAD_REQUEST)

        # check job target status
        if not job.target.is_active:
            return Response('Job target has already been deleted',
                            status=status.HTTP_400_BAD_REQUEST)

        # Run job on an Application node
        job.run(will_delay=False)

        return Response('Success to run command')


class SearchJob(APIView):
    authentication_classes = (AironeTokenAuth, BasicAuthentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    @airone_profile
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

        query = _update_query_by_get_param(Q(), 'operation', 'operation')
        query = _update_query_by_get_param(query, 'target__id', 'target_id')

        if not query.children:
            return Response("You have to specify (at least one) condition to search",
                            status=status.HTTP_400_BAD_REQUEST)

        jobs = Job.objects.filter(query).order_by('-created_at')
        if not jobs:
            return Response('There is no job that is matched specified condition',
                            status=status.HTTP_404_NOT_FOUND)

        return Response({'result': [x.to_json() for x in jobs]},
                        content_type='application/json; charset=UTF-8')
