import json

import mock
from django.conf import settings

from airone.celery import app
from airone.lib.test import AironeTestCase
from entity.models import Entity
from entry.models import Entry
from job.models import Job, JobOperation, JobTarget
from user.models import User


class ModelTest(AironeTestCase):
    def setUp(self):
        super(ModelTest, self).setUp()
        self.guest = User.objects.create(username="guest", password="passwd", is_superuser=False)
        self.admin = User.objects.create(username="admin", password="passwd", is_superuser=True)
        self.entity = Entity.objects.create(name="entity", created_user=self.guest)
        self.entry = Entry.objects.create(name="entry", created_user=self.guest, schema=self.entity)
        self.test_data = None

    def test_create_object(self):
        jobinfos = [
            {"method": "new_create", "op": JobOperation.CREATE_ENTRY.value},
            {"method": "new_edit", "op": JobOperation.EDIT_ENTRY.value},
            {"method": "new_delete", "op": JobOperation.DELETE_ENTRY.value},
            {"method": "new_copy", "op": JobOperation.COPY_ENTRY.value},
        ]
        for info in jobinfos:
            job = getattr(Job, info["method"])(self.guest, self.entry)

            self.assertEqual(job.user, self.guest)
            self.assertEqual(job.target, self.entry)
            self.assertEqual(job.target_type, JobTarget.ENTRY.value)
            self.assertEqual(job.status, Job.STATUS["PREPARING"])
            self.assertEqual(job.operation, info["op"])

    def test_get_object(self):
        params = {
            "entities": self.entity.id,
            "attrinfo": {"name": "foo", "keyword": ""},
            "export_style": '"yaml"',
        }

        # check there is no job
        self.assertFalse(Job.get_job_with_params(self.guest, params).exists())

        # create a new job
        job = Job.new_export(self.guest, text="hoge", params=params)
        self.assertEqual(job.target_type, JobTarget.UNKNOWN.value)
        self.assertEqual(job.operation, JobOperation.EXPORT_ENTRY.value)
        self.assertEqual(job.text, "hoge")

        # check created job is got by specified params
        self.assertEqual(Job.get_job_with_params(self.guest, params).count(), 1)
        self.assertEqual(Job.get_job_with_params(self.guest, params).last(), job)

        # check the case when different params is specified then it returns None
        params["attrinfo"]["name"] = ""
        self.assertFalse(Job.get_job_with_params(self.guest, params).exists())

    def test_cache(self):
        job = Job.new_create(self.guest, self.entry)

        registering_values = [
            1234,
            "foo\nbar\nbaz",
            ["foo", "bar"],
            {"hoge": "fuga", "foo": ["a", "b"]},
        ]
        for value in registering_values:
            job.set_cache(json.dumps(value))
            self.assertEqual(job.get_cache(), json.dumps(value))

    def test_dependent_job(self):
        (job1, job2) = [Job.new_edit(self.guest, self.entry) for x in range(2)]
        self.assertIsNone(job1.dependent_job)
        self.assertEqual(job2.dependent_job, job1)

        # When a job don't has target parameter, dependent_job is not set because
        # there is no problem when these tasks are run simultaneouslly.
        jobs = [Job.new_export(self.guest) for x in range(2)]
        self.assertTrue(all([j.dependent_job is None for j in jobs]))

        # overwrite timeout timeout value for testing
        settings.AIRONE["JOB_TIMEOUT"] = -1

        # Because jobs[1] is created after the expiry of jobs[0]
        jobs = [Job.new_edit(self.guest, self.entry) for x in range(2)]
        self.assertTrue(all([j.dependent_job is None for j in jobs]))

    def test_job_is_timeout(self):
        job = Job.new_create(self.guest, self.entry)
        self.assertFalse(job.is_timeout())

        # overwrite timeout timeout value for testing
        settings.AIRONE["JOB_TIMEOUT"] = -1

        self.assertTrue(job.is_timeout())

    def test_is_finished(self):
        job = Job.new_create(self.guest, self.entry)

        for status in [
            Job.STATUS["DONE"],
            Job.STATUS["ERROR"],
            Job.STATUS["TIMEOUT"],
            Job.STATUS["CANCELED"],
            Job.STATUS["WARNING"],
        ]:
            job.status = status
            job.save(update_fields=["status"])
            self.assertTrue(job.is_finished())

    def test_is_canceled(self):
        job = Job.new_create(self.guest, self.entry)

        self.assertFalse(job.is_canceled())

        # change status of target job
        job.update(Job.STATUS["CANCELED"])

        # confirms that is_canceled would be true by changing job status parameter
        self.assertTrue(job.is_canceled())

    def test_update_method(self):
        job = Job.new_create(self.guest, self.entry, "original text")
        self.assertEqual(job.status, Job.STATUS["PREPARING"])
        self.assertEqual(job.operation, JobOperation.CREATE_ENTRY.value)
        last_updated_time = job.updated_at

        # When an invalid status value is specified, status value won't be changed
        job.update(9999)
        job.refresh_from_db()

        self.assertEqual(job.status, Job.STATUS["PREPARING"])
        self.assertEqual(job.text, "original text")
        self.assertEqual(job.target.id, self.entry.id)
        self.assertEqual(job.operation, JobOperation.CREATE_ENTRY.value)
        self.assertGreater(job.updated_at, last_updated_time)
        last_updated_time = job.updated_at

        # update only status parameter
        job.update(Job.STATUS["PROCESSING"])
        job.refresh_from_db()

        self.assertEqual(job.status, Job.STATUS["PROCESSING"])
        self.assertEqual(job.text, "original text")
        self.assertEqual(job.target.id, self.entry.id)
        self.assertEqual(job.operation, JobOperation.CREATE_ENTRY.value)
        self.assertGreater(job.updated_at, last_updated_time)
        last_updated_time = job.updated_at

        # update status and text parameters
        job.update(Job.STATUS["CANCELED"], "changed message")
        job.refresh_from_db()
        self.assertEqual(job.status, Job.STATUS["CANCELED"])
        self.assertEqual(job.text, "changed message")
        self.assertEqual(job.target.id, self.entry.id)
        self.assertEqual(job.operation, JobOperation.CREATE_ENTRY.value)
        self.assertGreater(job.updated_at, last_updated_time)
        last_updated_time = job.updated_at

        # update status, text and target parameters
        new_entry = Entry.objects.create(name="newone", created_user=self.guest, schema=self.entity)
        job.update(Job.STATUS["DONE"], "further changed message", new_entry)
        job.refresh_from_db()

        self.assertEqual(job.status, Job.STATUS["DONE"])
        self.assertEqual(job.text, "further changed message")
        self.assertEqual(job.target.id, new_entry.id)
        self.assertEqual(job.operation, JobOperation.CREATE_ENTRY.value)
        self.assertGreater(job.updated_at, last_updated_time)

        # update invalid operation, job operation parameter won't be changed
        job.update(operation=9999)
        self.assertEqual(job.operation, JobOperation.CREATE_ENTRY.value)

        # update valid operation, job operation parameter will be changed
        job.update(operation=JobOperation.EDIT_ENTRY.value)
        self.assertEqual(job.operation, JobOperation.EDIT_ENTRY.value)

    def test_proceed_if_ready(self):
        job = Job.new_create(self.guest, self.entry)

        for status in [
            Job.STATUS["DONE"],
            Job.STATUS["ERROR"],
            Job.STATUS["TIMEOUT"],
            Job.STATUS["CANCELED"],
            Job.STATUS["PROCESSING"],
        ]:
            job.status = status
            job.save(update_fields=["status"])
            self.assertFalse(job.proceed_if_ready())

        job.status = Job.STATUS["PREPARING"]
        job.save(update_fields=["status"])
        self.assertTrue(job.proceed_if_ready())

    def test_may_schedule(self):
        # This describes how many times run method of Job called.
        self.test_data = 0

        def side_effect():
            self.test_data += 1

        [job1, job2] = [Job.new_create(self.guest, self.entry) for _ in range(2)]

        # Checks dependent_job parameters of both entries are set properly
        self.assertIsNone(job1.dependent_job)
        self.assertEqual(job2.dependent_job.id, job1.id)

        with mock.patch.object(Job, "run") as mock_run:
            mock_run.side_effect = side_effect

            # job1 doesn't have dependent job and ready to run so this never be rescheduled
            self.assertTrue(job1.proceed_if_ready())
            self.assertFalse(job1.may_schedule())
            self.assertEqual(self.test_data, 0)

            # job2 depends on job1 so this will be rescheduled by calling run method
            self.assertTrue(job2.may_schedule())
            self.assertEqual(self.test_data, 1)

            # This checks proceed_if_ready() method also call rescheduling method
            self.assertFalse(job2.proceed_if_ready())
            self.assertEqual(self.test_data, 2)

    def test_may_schedule_with_parallelizable_operation(self):
        [job1, job2] = [Job.new_notify_update_entry(self.guest, self.entry) for _ in range(2)]
        self.assertEqual(job2.dependent_job, job1)
        self.assertEqual(job1.status, Job.STATUS["PREPARING"])
        self.assertTrue(job2.proceed_if_ready())

    @mock.patch("job.models.import_module")
    def test_task_module(self, mock_import_module):
        # This initializes test data that describes how many times does import_module is called
        # in the processing actually.
        self.test_data = 0

        def side_effect(component):
            self.test_data += 1

        mock_import_module.side_effect = side_effect

        # create a job and call get_task_module method many times
        job = Job.new_create(self.guest, self.entry)
        for _x in range(3):
            job.get_task_module("hoge")

        # This confirms import_module method is invoked just one time even through get_task_module
        # is called multiple times.
        self.assertEqual(self.test_data, 1)

    def test_method_table(self):
        method_table = Job.method_table()

        # This confirms the number of JobOperation and method_table count is same
        self.assertEqual(len(method_table), len(JobOperation))

        # This confirms all operations of JobOperation are registered
        self.assertTrue(all([x.value in method_table for x in JobOperation]))

    def test_register_method_table(self):
        @app.task(bind=True)
        def custom_method(self, job_id):
            return "result of custom_method"

        @app.task(bind=True)
        def another_custom_method(self, job_id):
            return "result of another_custom_method"

        # register custom operation and method
        Job.register_method_table("custom_operation", custom_method)

        job = Job.new_create(self.guest, self.entry)
        job.operation = "custom_operation"

        # run job and check custom_method is called properly
        self.assertEqual(job.run(will_delay=False), "result of custom_method")

        # check unable to overwrite method when specified operation has already registered.
        Job.register_method_table("custom_operation", another_custom_method)
        self.assertEqual(job.run(will_delay=False), "result of custom_method")
