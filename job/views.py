import errno
import io
from datetime import datetime, timezone

from django.db.models import Q
from django.http import HttpResponse

# libraries of AirOne
from airone.lib.http import get_download_response, http_get, render

# related models in AirOne
from job.models import Job, JobOperation

# configuration of this app
from .settings import CONFIG


@http_get
def index(request):
    limitation = CONFIG.MAX_LIST_VIEW
    if request.GET.get("nolimit", None):
        limitation = None

    export_operations = [
        JobOperation.EXPORT_ENTRY,
        JobOperation.EXPORT_SEARCH_RESULT,
    ]

    query = Q(Q(user=request.user), ~Q(operation__in=Job.HIDDEN_OPERATIONS))
    context = {
        "jobs": [
            {
                "id": x.id,
                "target": x.target,
                "text": x.text,
                "status": x.status,
                "operation": x.operation,
                "can_cancel": x.operation in Job.CANCELABLE_OPERATIONS,
                "created_at": x.created_at,
                "passed_time": (x.updated_at - x.created_at).seconds
                if x.is_finished()
                else (datetime.now(timezone.utc) - x.created_at).seconds,
            }
            for x in Job.objects.filter(query).order_by("-created_at")[:limitation]
            if (
                x.operation in export_operations
                or (x.operation not in export_operations and x.target and x.target.is_active)
                or (x.operation == JobOperation.DELETE_ENTITY and x.target)
                or (x.operation == JobOperation.DELETE_ENTRY and x.target)
            )
        ]
    }

    return render(request, "list_jobs.html", context)


@http_get
def download(request, job_id):
    job = Job.objects.filter(id=job_id).first()
    if not job:
        return HttpResponse("Invalid Job-ID is specified", status=400)

    if job.user.id != request.user.id:
        return HttpResponse("Target Job is executed by other people", status=400)

    if job.operation not in Job.DOWNLOADABLE_OPERATIONS:
        return HttpResponse("Target Job has no value to return", status=400)

    # get value associated this Job from cache
    io_stream = io.StringIO()
    try:
        io_stream.write(job.get_cache())
    except OSError as e:
        # errno.ENOENT is the errno of FileNotFoundError
        if e.errno == errno.ENOENT:
            return HttpResponse("This result is no longer available", status=400)

    return get_download_response(io_stream, job.text)
