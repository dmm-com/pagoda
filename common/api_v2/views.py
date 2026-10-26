from typing import Any, cast

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from airone.lib.drf import InvalidValueError, YAMLParser
from common.api_v2.serializers import CommonImportJobSerializer
from common.lib.import_detector import ImportType, UnknownImportFormatError, detect_import_type
from common.lib.import_services import ImportDataError, validate_user_import_data
from entity.api_v2.serializers import EntityImportExportRootSerializer
from entry.api_v2.serializers import EntryImportSerializer
from entry.import_service import start_entry_import_jobs
from group.api_v2.serializers import GroupImportSerializer
from job.models import Job
from role.api_v2.serializers import RoleImportSerializer
from user.api_v2.serializers import UserImportSerializer
from user.models import User


def _parse_preview_job_id(request: Request) -> int | None:
    raw = request.query_params.get("preview_job_id")
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        raise InvalidValueError("'preview_job_id' must be an integer")


class CommonImportAPI(generics.GenericAPIView[Any]):
    """Import any kind of model, item, user, group or role file through a single endpoint.

    The kind of the file (model, item, user, group or role) is detected from its
    content. A file that matches none of them is rejected with 400 before any job
    is created. Applying the file always runs as a job.
    """

    parser_classes = [YAMLParser]
    permission_classes = [IsAuthenticated]
    serializer_class = CommonImportJobSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("force", OpenApiTypes.BOOL, OpenApiParameter.QUERY, default=False),
            OpenApiParameter(
                "preview_job_id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="The preview an item import was approved from.",
            ),
        ],
        request=OpenApiTypes.OBJECT,
        responses={200: CommonImportJobSerializer},
    )
    def post(self, request: Request) -> Response:
        user = cast("User", request.user)

        try:
            import_type = detect_import_type(request.data)
        except UnknownImportFormatError as e:
            raise ValidationError(str(e))

        # Writing a model or an item needs a writable account, while an import of
        # users, groups or roles can rewrite any of them and is for superusers.
        if import_type in (ImportType.ENTITY, ImportType.ENTRY):
            if user.is_readonly:
                return Response(status=status.HTTP_403_FORBIDDEN)
        elif not user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)

        job_ids: list[int] = []
        error_list: list[str] = []
        if import_type == ImportType.ENTITY:
            serializer = EntityImportExportRootSerializer(
                data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            job_ids.append(self._start_general_job(user, "entity", serializer.initial_data))
        elif import_type == ImportType.ENTRY:
            preview_job_id = _parse_preview_job_id(request)
            serializer = EntryImportSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            job_ids, error_list = start_entry_import_jobs(
                user,
                serializer.validated_data,
                force=request.query_params.get("force", "") in ["true", "True"],
                preview_job_id=preview_job_id,
            )
        elif import_type == ImportType.USER:
            serializer = UserImportSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            try:
                validate_user_import_data(request.data)
            except ImportDataError as e:
                raise ValidationError(str(e))
            job_ids.append(self._start_general_job(user, "user", request.data))
        elif import_type == ImportType.GROUP:
            serializer = GroupImportSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            job_ids.append(self._start_general_job(user, "group", request.data))
        else:
            serializer = RoleImportSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            job = Job.new_role_import_v2(
                user, text="Preparing to import role data", params=serializer.validated_data
            )
            job.run()
            job_ids.append(job.id)

        return Response(
            {"type": import_type.value, "job_ids": job_ids, "error": error_list},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _start_general_job(user: User, kind: str, data: Any) -> int:
        job = Job.new_import_general_v2(user, kind, data)
        job.run()
        return job.id
