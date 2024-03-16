import functools
from typing import Any, Callable

from job.models import Job, JobStatus


def may_schedule_until_job_is_ready(
    func: Callable[[Any, Job], JobStatus | tuple[JobStatus, str] | None],
):
    @functools.wraps(func)
    def wrapper(kls, job_id: int):
        job = Job.objects.get(id=job_id)
        if job.proceed_if_ready():
            # update Job status from PREPARING to PROCEEDING
            job.update(JobStatus.PROCESSING.value)

            try:
                # running Job processing
                ret: JobStatus | tuple[int, str] | None = func(kls, job)
            except Exception:
                ret = JobStatus.ERROR

            # update Job status after finishing Job processing
            if isinstance(ret, JobStatus):
                job.update(status=ret.value)
            elif (
                isinstance(ret, tuple) and isinstance(ret[0], JobStatus) and isinstance(ret[1], str)
            ):
                job.update(status=ret[0].value, text=ret[1])
            elif not job.is_canceled():
                job.update(JobStatus.DONE.value)

    return wrapper
