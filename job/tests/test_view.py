import json

from airone.lib.test import AironeViewTest
from django.urls import reverse
from entry import tasks
from entry.models import Entry
from entity.models import Entity
from job.settings import CONFIG
from job.models import Job, JobOperation

from requests_html import HTML
from unittest.mock import patch
from unittest.mock import Mock

# constants using this tests
_TEST_MAX_LIST_VIEW = 2


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        # save original configuration not to make affect other tests by chaning this
        self.old_config = CONFIG.conf

        CONFIG.conf["MAX_LIST_VIEW"] = _TEST_MAX_LIST_VIEW

    def tearDown(self):
        super(ViewTest, self).tearDown()

        # retrieve original configuration for Job.settings.CONFIG
        CONFIG.conf = self.old_config

    def test_get_jobs(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)

        # create three jobs
        [Job.new_create(user, entry) for _ in range(0, _TEST_MAX_LIST_VIEW + 1)]
        self.assertEqual(Job.objects.filter(user=user).count(), _TEST_MAX_LIST_VIEW + 1)

        # checks number of the returned objects are as expected
        resp = self.client.get("/job/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed("list_jobs.html")
        self.assertEqual(len(resp.context["jobs"]), _TEST_MAX_LIST_VIEW)

        for i, job in enumerate(
            Job.objects.filter(user=user).order_by("-created_at")[:_TEST_MAX_LIST_VIEW]
        ):
            self.assertEqual(resp.context["jobs"][i]["id"], job.id)
            self.assertEqual(resp.context["jobs"][i]["target"], job.target)
            self.assertEqual(resp.context["jobs"][i]["text"], job.text)
            self.assertEqual(resp.context["jobs"][i]["status"], job.status)
            self.assertEqual(resp.context["jobs"][i]["operation"], job.operation)
            self.assertEqual(resp.context["jobs"][i]["can_cancel"], True)
            self.assertEqual(resp.context["jobs"][i]["created_at"], job.created_at)
            self.assertEqual(resp.context["jobs"][i]["operation"], job.operation)
            self.assertGreaterEqual(resp.context["jobs"][i]["passed_time"], 0)

        # checks all job objects will be returned
        resp = self.client.get("/job/?nolimit=1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["jobs"]), _TEST_MAX_LIST_VIEW + 1)

        # checks no job object will be returned because of different user
        self.admin_login()
        resp = self.client.get("/job/?nolimit=1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["jobs"]), 0)

    def test_get_jobs_deleted_target(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        Job.new_create(user, entry)

        resp = self.client.get("/job/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["jobs"]), 1)

        # check the case show jobs after deleting job target
        entry.delete()

        # Create delete job
        Job.new_delete(user, entry)

        resp = self.client.get("/job/")
        self.assertEqual(resp.status_code, 200)

        # Confirm that the delete job can be obtained
        self.assertEqual(len(resp.context["jobs"]), 1)
        self.assertEqual(
            resp.context["jobs"][0]["operation"], JobOperation.DELETE_ENTRY.value
        )

        # check respond HTML has expected elements which are specified of CSS selectors
        parser = HTML(html=resp.content.decode("utf-8"))
        job_elems = parser.find("#entry_container .job_info")
        self.assertEqual(len(job_elems), 1)
        for job_elem in job_elems:
            for _cls in [
                "target",
                "status",
                "execution_time",
                "created_at",
                "note",
                "operation",
            ]:
                self.assertIsNotNone(job_elem.find(".%s" % _cls))

    def test_get_non_target_job(self):
        user = self.guest_login()

        Job.new_create(user, None)

        resp = self.client.get("/job/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["jobs"]), 0)

    def test_get_exporting_job(self):
        user = self.guest_login()

        # create jobs which are related with export
        Job.new_export(user),
        Job.new_export_search_result(user),

        resp = self.client.get("/job/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["jobs"]), 2)

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=tasks.create_entry_attrs),
    )
    def test_rerun_job_which_is_under_processing(self):
        # send a request to re-run creating entry which is under processing
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)

        params = {
            "entry_name": "new_entry",
            "attrs": [],
        }

        def side_effect():
            # send re-run request for executing job by calling API
            job = Job.objects.last()
            self.assertEqual(job.status, Job.STATUS["PROCESSING"])

            # check that backend processing never run by calling API
            resp = self.client.post("/api/v1/job/run/%d" % job.id)
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.content, b'"Target job is under processing"')

        with patch.object(Entry, "register_es", Mock(side_effect=side_effect)):
            resp = self.client.post(
                reverse("entry:do_create", args=[entity.id]),
                json.dumps(params),
                "application/json",
            )

            self.assertEqual(resp.status_code, 200)

    def test_job_download_failure(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)

        job = Job.new_create(user, entity, "hoge")

        # When user send a download request of Job with invalid Job-id, then HTTP 400 is returned
        resp = self.client.get("/job/download/%d" % (job.id + 1))
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode(), "Invalid Job-ID is specified")

        # When user send a download request of non export Job, then HTTP 400 is returned
        resp = self.client.get("/job/download/%d" % job.id)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode(), "Target Job has no value to return")

        # The case user sends a download request for a job which doesn't have a result
        job = Job.new_export(user, text="fuga")
        resp = self.client.get("/job/download/%d" % job.id)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode(), "This result is no longer available")

        # When user send a download request of export Job by differenct user from creating one,
        # then HTTP 400 is returned
        job = Job.new_export(user, text="fuga")
        user = self.admin_login()
        resp = self.client.get("/job/download/%d" % job.id)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.content.decode(), "Target Job is executed by other people"
        )

    def test_job_download_exported_result(self):
        user = self.guest_login()

        # initialize an export Job
        job = Job.new_export(user, text="hoge")
        job.set_cache("abcd")

        # check job contents could be downloaded
        resp = self.client.get("/job/download/%d" % job.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Disposition"], 'attachment; filename="hoge"')
        self.assertEqual(resp.content.decode("utf8"), "abcd")

    def test_job_download_exported_search_result(self):
        user = self.guest_login()

        # initialize an export Job
        job = Job.new_export_search_result(user, text="hoge")
        job.set_cache("abcd")

        # check job contents could be downloaded
        resp = self.client.get("/job/download/%d" % job.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Disposition"], 'attachment; filename="hoge"')
        self.assertEqual(resp.content.decode("utf8"), "abcd")

    def test_hidden_jobs_is_not_shown(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        # create a hidden job
        Job.new_register_referrals(user, entry)

        # create an unhidden job
        Job.new_create(user, entry)

        # access job list page and check only unhidden jobs are returned
        resp = self.client.get("/job/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["jobs"]), 1)
        self.assertEqual(
            resp.context["jobs"][0]["operation"], JobOperation.CREATE_ENTRY.value
        )
