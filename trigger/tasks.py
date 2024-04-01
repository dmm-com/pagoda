import json

from airone.celery import app
from airone.lib.job import may_schedule_until_job_is_ready
from entry.models import Entry
from job.models import Job, JobStatus
from trigger.models import (
    TriggerCondition,
)
from user.models import User


@app.task(bind=True)
@may_schedule_until_job_is_ready
def may_invoke_trigger(self, job: Job) -> JobStatus:
    # Get job parameters that are set at frontend processing
    user = User.objects.filter(id=job.user.id).first()
    entry = Entry.objects.filter(id=job.target.id, is_active=True).first()
    recv_data = json.loads(job.params)

    # Get TriggerAction instances from entity and user specified data, then run them.
    for action in TriggerCondition.get_invoked_actions(entry.schema, recv_data):
        action.run(user, entry)

    return JobStatus.DONE
