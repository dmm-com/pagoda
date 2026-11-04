import csv
import errno
import io
from datetime import timedelta
from typing import Any, cast

from django.db.models import Q, QuerySet
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response

from airone.lib.acl import ACLObjType
from airone.lib.drf import FileIsNotExistsError, InvalidValueError, JobIsNotDoneError
from airone.lib.http import get_download_response
from airone.lib.import_preview import PREVIEW_SUMMARY_KEYS
from entry.models import Entry
from job.api_v2.serializers import ImportPreviewSerializer, JobSerializers
from job.models import Job, JobOperation, JobStatus
from user.models import User


class JobAPI(viewsets.ModelViewSet[Job]):
    serializer_class = JobSerializers

    def get_queryset(self) -> QuerySet[Job]:
        user = cast(User, self.request.user)
        if user.is_superuser:
            return Job.objects.all()
        return Job.objects.filter(user=user)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        job: Job = self.get_object()

        if job.user != request.user:
            return Response("Cannot cancel another user's job", status=status.HTTP_403_FORBIDDEN)

        if job.status == JobStatus.DONE:
            return Response("Target job has already been done", status=status.HTTP_400_BAD_REQUEST)

        if job.operation not in Job.CANCELABLE_OPERATIONS:
            return Response("Target job cannot be canceled", status=status.HTTP_400_BAD_REQUEST)

        # update job.status to be canceled
        job.update(JobStatus.CANCELED)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "encode",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                enum=["utf-8", "shift_jis"],
                default="utf-8",
            ),
        ],
    )
    def download(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        job: Job = self.get_object()

        if job.user != request.user:
            return Response("Cannot download another user's job", status=status.HTTP_403_FORBIDDEN)

        encode_param = request.query_params.get("encode", "utf-8")

        if encode_param not in ["utf-8", "shift_jis"]:
            raise InvalidValueError("Invalid encode parameter")

        if job.operation not in Job.DOWNLOADABLE_OPERATIONS:
            raise InvalidValueError("Target job cannot be downloaded")

        if job.status != JobStatus.DONE:
            raise JobIsNotDoneError("Target job has not yet done")

        # get value associated this Job from cache
        io_stream = io.StringIO()
        try:
            io_stream.write(job.get_cache())
        except OSError as e:
            # errno.ENOENT is the errno of FileNotFoundError
            if e.errno == errno.ENOENT:
                raise FileIsNotExistsError("Target file is not exists")

        return cast(Response, get_download_response(io_stream, job.text, encode_param))

    @extend_schema(
        parameters=[
            OpenApiParameter("offset", OpenApiTypes.INT, OpenApiParameter.QUERY, default=0),
            OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY, default=100),
            OpenApiParameter(
                "action",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description=(
                    "Comma-separated actions to list, e.g. 'error,skip'. "
                    "Defaults to every action. The summary always covers them all."
                ),
            ),
        ],
        responses={200: ImportPreviewSerializer},
    )
    def preview(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Return the result of a preview job, one page of rows at a time.

        The whole preview is kept as a single cached payload, so the rows are
        paged out from here rather than queried: a preview of a large file can
        run to thousands of rows, and no client wants them in one response.

        The rows a user came for -- the errors, the changes -- may sit anywhere
        in a long file, so they are filtered here rather than after paging.
        """
        job: Job = self.get_object()

        if job.user != request.user:
            return Response("Cannot read another user's job", status=status.HTTP_403_FORBIDDEN)

        if job.operation not in Job.PREVIEW_OPERATIONS:
            raise InvalidValueError("Target job has no preview")

        if job.status != JobStatus.DONE:
            raise JobIsNotDoneError("Target job has not yet done")

        try:
            payload = job.get_cache()
        except OSError as e:
            # errno.ENOENT is the errno of FileNotFoundError
            if e.errno == errno.ENOENT:
                raise FileIsNotExistsError("Target file is not exists")
            raise

        rows = _filter_by_action(payload["rows"], request.query_params.get("action"))
        offset = _query_int(request, "offset", default=0)
        limit = _query_int(request, "limit", default=100)

        return Response(
            {
                "summary": payload["summary"],
                "count": len(rows),
                "truncated": payload["truncated"],
                "rows": [_public_row(row) for row in rows[offset : offset + limit]],
            }
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "encode",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                enum=["utf-8", "shift_jis"],
                default="utf-8",
            ),
        ],
        responses={200: OpenApiTypes.STR},
    )
    def preview_download(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Download a whole preview as CSV.

        A preview of a large file is worth reading carefully, and a browser table
        is not where that is done. This hands over every row that was kept, in
        the order the file listed them.
        """
        job: Job = self.get_object()

        if job.user != request.user:
            return Response("Cannot read another user's job", status=status.HTTP_403_FORBIDDEN)

        if job.operation not in Job.PREVIEW_OPERATIONS:
            raise InvalidValueError("Target job has no preview")

        if job.status != JobStatus.DONE:
            raise JobIsNotDoneError("Target job has not yet done")

        encode_param = request.query_params.get("encode", "utf-8")
        if encode_param not in ["utf-8", "shift_jis"]:
            raise InvalidValueError("Invalid encode parameter")

        try:
            payload = job.get_cache()
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise FileIsNotExistsError("Target file is not exists")
            raise

        io_stream = io.StringIO()
        writer = csv.writer(io_stream)
        writer.writerow(["kind", "name", "action", "reason", "changes", "will_invoke_trigger"])
        for row in payload["rows"]:
            writer.writerow(
                [
                    row["kind"],
                    row["name"],
                    row["action"],
                    row["reason"] or "",
                    " / ".join(
                        "%s: %s -> %s" % (c["field"], c["before"] or "", c["after"] or "")
                        for c in row["changes"]
                    ),
                    row.get("will_invoke_trigger", False),
                ]
            )

        return cast(Response, get_download_response(io_stream, "import_preview.csv", encode_param))


# Keys a preview keeps for the import's own use, which no client should receive.
INTERNAL_PREVIEW_KEYS = frozenset({"baseline"})


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in INTERNAL_PREVIEW_KEYS}


def _filter_by_action(rows: list[dict[str, Any]], action: str | None) -> list[dict[str, Any]]:
    if not action:
        return rows

    wanted = {x.strip() for x in action.split(",") if x.strip()}
    unknown = wanted - set(PREVIEW_SUMMARY_KEYS)
    if unknown:
        raise InvalidValueError("Unknown action: %s" % ", ".join(sorted(unknown)))

    return [row for row in rows if row["action"] in wanted]


def _query_int(request: Request, name: str, default: int) -> int:
    raw = request.query_params.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise InvalidValueError("'%s' must be an integer" % name)
    if value < 0:
        raise InvalidValueError("'%s' must not be negative" % name)
    return value


@extend_schema(
    parameters=[
        OpenApiParameter("created_after", OpenApiTypes.DATETIME, OpenApiParameter.QUERY),
        OpenApiParameter("created_before", OpenApiTypes.DATETIME, OpenApiParameter.QUERY),
        OpenApiParameter("target_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("job_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("status", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter(
            "operation",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="One operation ID or comma-separated operation IDs.",
        ),
        OpenApiParameter(
            "user",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Case-insensitive partial match on username.",
        ),
        OpenApiParameter(
            "text",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Case-insensitive partial match on job message.",
        ),
        OpenApiParameter(
            "all_users",
            OpenApiTypes.BOOL,
            OpenApiParameter.QUERY,
            description="If true and the requester is a superuser, return jobs for all users.",
            default=False,
        ),
    ],
)
class JobListAPI(viewsets.ModelViewSet[Job]):
    serializer_class = JobSerializers
    pagination_class = LimitOffsetPagination

    def get_queryset(self) -> QuerySet[Job]:
        user = self.request.user
        params = self.request.query_params
        all_users: bool = user.is_superuser and params.get("all_users", "false").lower() == "true"

        targetless_visible_operations: list[JobOperation] = [
            JobOperation.EXPORT_CONFIGURATION_V2,
            JobOperation.EXPORT_ENTRY,
            JobOperation.EXPORT_ENTRY_V2,
            JobOperation.EXPORT_SEARCH_RESULT,
            JobOperation.EXPORT_SEARCH_RESULT_V2,
            JobOperation.IMPORT_ROLE_V2,
        ]
        query = Q() if all_users else Q(user=user)
        query &= ~Q(operation__in=Job.HIDDEN_OPERATIONS)
        query &= Q(
            Q(operation__in=targetless_visible_operations, target__isnull=True)
            | Q(target__isnull=False, target__is_active=True)
        )

        for name, lookup in (
            ("created_after", "created_at__gte"),
            ("created_before", "created_at__lte"),
        ):
            raw = params.get(name)
            if raw:
                try:
                    value = parse_datetime(raw)
                except ValueError:
                    value = None
                if value is None:
                    raise InvalidValueError("'%s' must be a datetime" % name)
                if timezone.is_naive(value):
                    value = timezone.make_aware(value)
                query &= Q(**{lookup: value})

        for name, lookup in (
            ("target_id", "target_id"),
            ("job_id", "id"),
        ):
            raw = params.get(name)
            if raw:
                try:
                    value = int(raw)
                except ValueError:
                    raise InvalidValueError("'%s' must be an integer" % name)
                if value < 0:
                    raise InvalidValueError("'%s' must not be negative" % name)
                query &= Q(**{lookup: value})

        raw_operations = params.get("operation")
        if raw_operations:
            try:
                operations = [int(value) for value in raw_operations.split(",")]
            except ValueError:
                raise InvalidValueError("'operation' must contain integers")
            if any(value < 0 for value in operations):
                raise InvalidValueError("'operation' must not contain negative integers")
            query &= Q(operation__in=operations)

        raw_status = params.get("status")
        if raw_status:
            try:
                job_status = int(raw_status)
            except ValueError:
                raise InvalidValueError("'status' must be an integer")
            if job_status < 0:
                raise InvalidValueError("'status' must not be negative")
            timeout_at = timezone.now() - timedelta(seconds=Job._get_job_timeout())
            if job_status == JobStatus.TIMEOUT:
                query &= Q(status=JobStatus.TIMEOUT) | Q(
                    status__in=[JobStatus.PREPARING, JobStatus.PROCESSING],
                    updated_at__lt=timeout_at,
                )
            elif job_status in (JobStatus.PREPARING, JobStatus.PROCESSING):
                query &= Q(status=job_status, updated_at__gte=timeout_at)
            else:
                query &= Q(status=job_status)

        jobs = Job.objects.filter(query)
        if params.get("user"):
            jobs = jobs.alias(search_user=Lower("user__username")).filter(
                search_user__contains=params["user"].strip().lower()
            )
        if params.get("text"):
            jobs = jobs.alias(search_text=Lower("text")).filter(
                search_text__contains=params["text"].strip().lower()
            )

        return jobs.select_related("user", "target").defer("params").order_by("-id")

    def paginate_queryset(self, queryset: Any) -> Any:
        page = super().paginate_queryset(queryset)
        self._paginated_page = page
        return page

    def get_serializer_context(self) -> dict[str, Any]:
        context: dict[str, Any] = dict(super().get_serializer_context())

        # prefetch target entries, then pass it via context manually to avoid N+1 in serializer
        page: list[Job] = getattr(self, "_paginated_page", None) or []
        target_ids = [
            obj.target.id
            for obj in page
            if obj.target is not None and obj.target.objtype == ACLObjType.Entry
        ]
        entries = (
            Entry.objects.filter(id__in=target_ids)
            .select_related("schema")
            .values("id", "name", "schema__id", "schema__name")
        )
        context[JobSerializers.PREFETCHED_ENTRIES_KEY] = {e["id"]: e for e in entries}

        return context
