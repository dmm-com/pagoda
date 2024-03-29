import json

from airone.celery import app
from airone.lib.job import may_schedule_until_job_is_ready
from job.models import Job, JobStatus
from role.models import Role


@app.task(bind=True)
@may_schedule_until_job_is_ready
def edit_role_referrals(self, job: Job) -> JobStatus:
    params = json.loads(job.params)
    role = Role.objects.get(id=params["role_id"])

    for entry in [x for x in role.get_referred_entries()]:
        entry.register_es()

    return JobStatus.DONE
