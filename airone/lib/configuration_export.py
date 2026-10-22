from typing import Any, cast

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from job.api_v2.serializers import JobSerializers
from job.models import Job
from user.models import User


class ConfigurationExportAPI(APIView):
    export_kind: str

    @extend_schema(responses={202: JobSerializers})
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        job = Job.new_export_configuration_v2(cast(User, request.user), self.export_kind)
        job.run()
        return Response(JobSerializers(job).data, status=status.HTTP_202_ACCEPTED)
