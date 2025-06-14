import json

from airone.celery import app
from airone.lib.job import may_schedule_until_job_is_ready, register_job_task
from group.models import Group
from job.models import Job, JobOperation, JobStatus


@register_job_task(JobOperation.GROUP_REGISTER_REFERRAL)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def edit_group_referrals(self, job: Job) -> JobStatus:
    params = json.loads(job.params)
    group = Group.objects.get(id=params["group_id"])

    for entry in [x for x in group.get_referred_entries()]:
        entry.register_es()

    return JobStatus.DONE
