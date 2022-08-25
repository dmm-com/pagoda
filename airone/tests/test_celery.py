from billiard.einfo import ExceptionInfo
from django.core import mail

from airone.celery import celery_task_failure_email, celery_task_failure_update_job_status
from airone.lib.test import AironeViewTest
from job.models import Job


class CeleryTest(AironeViewTest):
    def test_celery_task_failure_email(self):
        admins = [("admin", "airone@example.com")]
        task_name = "test_task"

        with self.settings(ADMINS=admins, EMAIL_SUBJECT_PREFIX=""):
            celery_task_failure_email(
                task_id="test_task_id",
                exception=Exception("test"),
                sender=type(
                    "task",
                    (object,),
                    {
                        "name": task_name,
                    },
                ),
                args=[],
                kwargs={},
                einfo=None,
            )

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].to, [a[1] for a in admins])
            self.assertEqual(mail.outbox[0].subject, "ERROR Celery Task %s" % task_name)

    def test_celery_task_failure_update_job_status(self):
        user = self.guest_login()
        job: Job = Job.objects.create(user=user, status=Job.STATUS["PROCESSING"])
        celery_task_failure_update_job_status(
            task_id="test_task_id",
            exception=Exception("Test"),
            args=[job.id],
            kwargs={},
            traceback=ExceptionInfo.traceback,
            einfo=ExceptionInfo,
        )
        job.refresh_from_db()
        self.assertEqual(job.status, Job.STATUS["ERROR"])
