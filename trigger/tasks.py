import json

from airone.celery import app
from job.models import Job
from user.models import User
from entry.models import Entry
from trigger.models import TriggerParentCondition, TriggerCondition, TriggerAction, TriggerActionValue


@app.task(bind=True)
def may_invoke_trigger(self, job_id):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        # At the first time, update job status to prevent executing this job duplicately
        job.update(Job.STATUS["PROCESSING"])

        # Get job parameters that are set at frontend processing
        user = User.objects.filter(id=job.user.id).first()
        entry = Entry.objects.filter(id=job.target.id, is_active=True).first()
        recv_data = json.loads(job.params)

        print("[onix/may_invoke_trigger(10)] recv_data: %s" % str(recv_data))

        # Get parent TriggerCondition instance from entity
        for parent_condition in TriggerParentCondition.objects.filter(entity=entry.schema):
            actions = parent_condition.get_actions([
                {"attr_id": x["id"], "value": x["value"]} for x in recv_data
            ])
            print("[onix/may_invoke_trigger(20)] actions: %s" % str(actions))

        job.update(Job.STATUS["DONE"])