from airone.celery import app
from entry.models import Attribute, Entry
from job.models import Job, JobStatus
from user.models import User


@app.task(bind=True)
def update_custom_attribute(self, job_id: str):
    job = Job.objects.get(id=job_id)

    if job.proceed_if_ready():
        # At the first time, update job status to prevent executing this job duplicately
        job.update(JobStatus.PROCESSING)

        user = User.objects.filter(id=job.user.id).first()
        entry = Entry.objects.filter(id=job.target.id, is_active=True).first()

        attr: Attribute = entry.attrs.filter(schema__name="val").first()
        if attr:
            attr.add_value(user, "initial value")

        job.status = JobStatus.DONE
        job.save(update_fields=["status"])
