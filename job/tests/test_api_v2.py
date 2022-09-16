from datetime import timedelta

from airone.lib.test import AironeViewTest
from entity.models import Entity
from entry.models import Entry
from job.models import Job, JobOperation

# constants using this tests
_TEST_MAX_LIST_VIEW = 2


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

    def tearDown(self):
        super(ViewTest, self).tearDown()

    def test_get_jobs(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)

        # create three jobs
        [Job.new_create(user, entry) for _ in range(0, _TEST_MAX_LIST_VIEW)]
        self.assertEqual(Job.objects.filter(user=user).count(), _TEST_MAX_LIST_VIEW)

        # checks number of the returned objects are as expected
        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], _TEST_MAX_LIST_VIEW)

        # checks no job object will be returned because of different user
        self.admin_login()
        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 0)

    def test_get_jobs_deleted_target(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        Job.new_create(user, entry)

        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 1)

        # check the case show jobs after deleting job target
        entry.delete()

        # Create delete job
        Job.new_delete(user, entry)

        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)

        # Confirm that the delete job can be obtained
        body = resp.json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["operation"], JobOperation.DELETE_ENTRY.value)

    def test_get_non_target_job(self):
        user = self.guest_login()

        Job.new_create(user, None)

        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 0)

    def test_get_exporting_job(self):
        user = self.guest_login()

        # create jobs which are related with export
        Job.new_export(user),
        Job.new_export_search_result(user),

        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 2)

    def test_get_recent_job(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        job = Job.new_create(user, entry, "hoge")

        # match the created_after
        created_after = job.created_at.strftime("%Y-%m-%d")
        resp = self.client.get(
            f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}"
            f"&offset=0&created_after={created_after}"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 1)

        # don't match the created_after
        created_after = (job.created_at + timedelta(days=1)).strftime("%Y-%m-%d")
        resp = self.client.get(
            f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}"
            f"&offset=0&created_after={created_after}"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 0)

    def test_get_job(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        job = Job.new_create(user, entry, "hoge")

        resp = self.client.get("/job/api/v2/%d/" % job.id)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["id"], job.id)
        self.assertEqual(body["status"], Job.STATUS["PREPARING"])
        self.assertEqual(body["text"], "hoge")

    def test_get_job_with_invalid_param(self):
        user = self.guest_login()
        resp = self.client.get("/job/api/v2/%d/" % 9999)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json(), {"detail": "Not found."})

        resp = self.client.get("/job/api/v2/%s/" % "hoge")
        self.assertEqual(resp.status_code, 404)

        # other user job
        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        job = Job.new_create(user, entry)

        self.admin_login()
        resp = self.client.get("/job/api/v2/%d/" % job.id)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json(), {"detail": "Not found."})
