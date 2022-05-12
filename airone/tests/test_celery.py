from airone.celery import celery_task_failure_email
from django.core import mail
from django.test import TestCase


class CeleryTest(TestCase):
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
