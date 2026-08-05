import csv
import errno
import io
from typing import Any, cast

from django.db.models import Q, QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status, viewsets
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
                "rows": rows[offset : offset + limit],
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
        OpenApiParameter("target_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
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
        created_after: str | None = self.request.query_params.get("created_after", None)
        target_id: str | None = self.request.query_params.get("target_id", None)
        all_users: bool = (
            user.is_superuser
            and self.request.query_params.get("all_users", "false").lower() == "true"
        )

        export_operations: list[JobOperation] = [
            JobOperation.EXPORT_ENTRY,
            JobOperation.EXPORT_ENTRY_V2,
            JobOperation.EXPORT_SEARCH_RESULT,
            JobOperation.EXPORT_SEARCH_RESULT_V2,
        ]
        query = Q(
            Q() if all_users else Q(user=user),
            ~Q(operation__in=Job.HIDDEN_OPERATIONS),
            Q(
                Q(operation__in=export_operations)
                | Q(
                    ~Q(operation__in=export_operations),
                    target__isnull=False,
                    target__is_active=True,
                )
                | Q(operation=JobOperation.DELETE_ENTITY, target__isnull=False)
                | Q(operation=JobOperation.DELETE_ENTRY, target__isnull=False)
                | Q(operation=JobOperation.DELETE_ENTITY_V2, target__isnull=False)
                | Q(operation=JobOperation.DELETE_ENTRY_V2, target__isnull=False)
            ),
        )

        if created_after:
            query &= Q(created_at__gte=created_after)
        if target_id:
            query &= Q(target=target_id)

        return Job.objects.filter(query).select_related("target").order_by("-created_at")

    def get_serializer_context(self) -> dict[str, Any]:
        context: dict[str, Any] = dict(super().get_serializer_context())

        # prefetch target entries, then pass it via context manually to avoid N+1 in serializer
        qs = self.paginate_queryset(self.get_queryset().values("target__id", "target__objtype"))
        target_ids = [
            int(r["target__id"]) for r in (qs or []) if r["target__objtype"] == ACLObjType.Entry
        ]
        entries = (
            Entry.objects.filter(id__in=target_ids)
            .select_related("schema")
            .values("id", "name", "schema__id", "schema__name")
        )
        context[JobSerializers.PREFETCHED_ENTRIES_KEY] = {e["id"]: e for e in entries}

        return context


@extend_schema(request=None, responses={200: OpenApiTypes.STR})
class JobRerunAPI(generics.UpdateAPIView[Job]):
    serializer_class = None

    def get_queryset(self) -> QuerySet[Job]:
        return Job.objects.filter(user=cast(User, self.request.user))

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response(
            "Unsupported. use PATCH alternatively", status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        job: Job = self.get_object()

        # check job status before starting processing
        if job.status == JobStatus.DONE:
            return Response("Target job has already been done")
        elif job.status == JobStatus.PROCESSING:
            return Response("Target job is under processing", status=status.HTTP_400_BAD_REQUEST)

        # check job target status
        if not job.target or not job.target.is_active:
            return Response(
                "Job target has already been deleted", status=status.HTTP_400_BAD_REQUEST
            )

        # Run job on an Application node
        job.run(will_delay=False)

        return Response("Success to run command")
