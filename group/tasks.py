import json

from airone.celery import app
from group.models import Group
from job.models import Job


@app.task(bind=True)
def edit_group_referrals(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        job.update(job.STATUS["PROCESSING"])
        params = json.loads(job.params)
        group = Group.objects.get(id=params["group_id"])

        for entry in [x for x in group.get_referred_entries()]:
            entry.register_es()

        job.update(Job.STATUS["DONE"])
