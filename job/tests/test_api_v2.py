from airone.lib.test import AironeViewTest

from job.models import Job, JobOperation
from entry.models import Entry
from entity.models import Entity

from job.settings import CONFIG

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
        resp = self.client.get("/job/api/v2/jobs")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), _TEST_MAX_LIST_VIEW)

        # checks all job objects will be returned
        resp = self.client.get("/job/api/v2/jobs?nolimit=1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), _TEST_MAX_LIST_VIEW + 1)

        # checks no job object will be returned because of different user
        self.admin_login()
        resp = self.client.get("/job/api/v2/jobs?nolimit=1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 0)

    def test_get_jobs_deleted_target(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        Job.new_create(user, entry)

        resp = self.client.get("/job/api/v2/jobs")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

        # check the case show jobs after deleting job target
        entry.delete()

        # Create delete job
        Job.new_delete(user, entry)

        resp = self.client.get("/job/api/v2/jobs")
        self.assertEqual(resp.status_code, 200)

        # Confirm that the delete job can be obtained
        body = resp.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["operation"], JobOperation.DELETE_ENTRY.value)

    def test_get_non_target_job(self):
        user = self.guest_login()

        Job.new_create(user, None)

        resp = self.client.get("/job/api/v2/jobs")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 0)

    def test_get_exporting_job(self):
        user = self.guest_login()

        # create jobs which are related with export
        Job.new_export(user),
        Job.new_export_search_result(user),

        resp = self.client.get("/job/api/v2/jobs")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)
