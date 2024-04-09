import functools
from typing import Any, Callable

from acl.models import ACLBase
from job.models import Job, JobStatus


def may_schedule_until_job_is_ready(
    func: Callable[[Any, Job], JobStatus | tuple[JobStatus, str, ACLBase | None] | None],
):
    @functools.wraps(func)
    def wrapper(kls, job_id: int):
        job = Job.objects.get(id=job_id)

        if not job.proceed_if_ready():
            return
        # update Job status from PREPARING to PROCEEDING
        job.update(JobStatus.PROCESSING)

        try:
            # running Job processing
            ret: JobStatus | tuple[JobStatus, str, ACLBase | None] | None = func(kls, job)
        except Exception:
            ret = JobStatus.ERROR

        # update Job status after finishing Job processing
        if isinstance(ret, JobStatus):
            job.update(status=ret)
        elif (
            isinstance(ret, tuple)
            and isinstance(ret[0], JobStatus)
            and isinstance(ret[1], str)
            and isinstance(ret[2], ACLBase | None)
        ):
            job.update(status=ret[0], text=ret[1], target=ret[2])
        elif not job.is_canceled():
            job.update(JobStatus.DONE)

    return wrapper
