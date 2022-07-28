import functools

from job.models import Job


def may_schedule_until_job_is_ready(func):
    @functools.wraps(func)
    def wrapper(kls, job_id):
        job = Job.objects.get(id=job_id)
        if job.proceed_if_ready():
            # update Job status from PREPARING to PROCEEDING
            job.update(Job.STATUS["PROCESSING"])

            # running Job processing
            ret = func(kls, job)

            # update Job status after finishing Job processing
            if isinstance(ret, int):
                job.update(status=ret)
            elif isinstance(ret, tuple) and len(ret) == 2:
                job.update(status=ret[0], text=ret[1])
            elif not job.is_canceled():
                job.update(Job.STATUS["DONE"])

    return wrapper
