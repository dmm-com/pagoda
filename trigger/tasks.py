import json

from airone.celery import app
from entry.models import Entry
from job.models import Job
from trigger.models import (
    TriggerCondition,
)
from user.models import User


@app.task(bind=True)
def may_invoke_trigger(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        # At the first time, update jobestatus to prevent executing this job duplicately
        job.update(Job.STATUS["PROCESSING"])

        # Get job parameters that are set at frontend processing
        user = User.objects.filter(id=job.user.id).first()
        entry = Entry.objects.filter(id=job.target.id, is_active=True).first()
        recv_data = json.loads(job.params)

        # Get TriggerAction instances from entity and user specified data, then run them.
        for action in TriggerCondition.get_invoked_actions(entry.schema, recv_data):
            action.run(user, entry)

        job.update(Job.STATUS["DONE"])
