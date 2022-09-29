import json

from airone.celery import app
from job.models import Job
from role.models import Role


@app.task(bind=True)
def edit_role_referrals(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        job.update(job.STATUS["PROCESSING"])
        params = json.loads(job.params)
        role = Role.objects.get(id=params["role_id"])

        for entry in [x for x in role.get_referred_entries()]:
            entry.register_es()

        job.update(Job.STATUS["DONE"])
