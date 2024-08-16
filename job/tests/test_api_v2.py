from datetime import timedelta

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrType
from entity.models import Entity, EntityAttr
from entry.models import Entry
from job.models import Job, JobOperation, JobStatus

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
        self.assertEqual(body["results"][0]["operation"], JobOperation.DELETE_ENTRY)

    def test_get_non_target_job(self):
        user = self.guest_login()

        Job.new_create(user, None)

        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 0)

    def test_get_exporting_job(self):
        user = self.guest_login()

        # create jobs which are related with export
        (Job.new_export(user),)
        (Job.new_export_search_result(user),)

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
        created_after = (job.created_at + timedelta(days=2)).strftime("%Y-%m-%d")
        resp = self.client.get(
            f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}"
            f"&offset=0&created_after={created_after}"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 0)

    def test_get_jobs_with_target_id(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry1 = Entry.objects.create(name="entry1", created_user=user, schema=entity)
        entry2 = Entry.objects.create(name="entry2", created_user=user, schema=entity)

        # create three jobs for entry1
        [Job.new_create(user, entry1) for _ in range(0, _TEST_MAX_LIST_VIEW)]
        self.assertEqual(Job.objects.filter(user=user).count(), _TEST_MAX_LIST_VIEW)
        # create one job for entry2
        Job.new_create(user, entry2)

        # checks number of the returned objects are for entry1
        resp = self.client.get(
            f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0&target_id={entry1.id}"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], _TEST_MAX_LIST_VIEW)

        # checks number of the returned objects are for both entry1 and entry2
        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], _TEST_MAX_LIST_VIEW + 1)

    def test_get_job(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        job = Job.new_create(user, entry, "hoge")

        resp = self.client.get("/job/api/v2/%d/" % job.id)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["id"], job.id)
        self.assertEqual(body["status"], JobStatus.PREPARING)
        self.assertEqual(body["text"], "hoge")

    def test_get_job_with_invalid_param(self):
        user = self.guest_login()
        resp = self.client.get("/job/api/v2/%d/" % 9999)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Job matches the given query."}
        )

        resp = self.client.get("/job/api/v2/%s/" % "hoge")
        self.assertEqual(resp.status_code, 404)

        # other user job
        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        job = Job.new_create(user, entry)

        self.admin_login()
        resp = self.client.get("/job/api/v2/%d/" % job.id)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Job matches the given query."}
        )

    def test_cancel_job(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        # make a job which isn't cancellable
        job = Job.new_delete(user, entry)
        self.assertEqual(job.status, JobStatus.PREPARING)

        # send request with invalid job id
        resp = self.client.delete("/job/api/v2/%d/" % 99999)
        self.assertEqual(resp.status_code, 404)

        # target jobs that cannot be canceled
        resp = self.client.delete("/job/api/v2/%d/" % job.id)
        self.assertEqual(resp.status_code, 400)

        # make a cancellable job
        job = Job.new_create(user, entry)
        self.assertEqual(job.status, JobStatus.PREPARING)
        resp = self.client.delete("/job/api/v2/%d/" % job.id)
        self.assertEqual(resp.status_code, 204)

    def test_rerun_jobs(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        attr = EntityAttr.objects.create(
            name="attr",
            created_user=user,
            type=AttrType.STRING,
            parent_entity=entity,
        )

        # make a job to create an entry
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)
        job = Job.new_create(
            user,
            entry,
            params={
                "attrs": [
                    {
                        "id": str(attr.id),
                        "value": [{"data": "hoge", "index": 0}],
                        "referral_key": [],
                    }
                ]
            },
        )

        # send request to run job
        resp = self.client.patch("/job/api/v2/%d/rerun" % job.id)
        self.assertEqual(resp.status_code, 200)

        job = Job.objects.get(id=job.id)
        self.assertEqual(job.status, JobStatus.DONE)
        self.assertEqual(entry.attrs.count(), 1)

        attrv = entry.attrs.first().get_latest_value()
        self.assertEqual(attrv.value, "hoge")

        # send request to run job with finished job-id
        resp = self.client.patch("/job/api/v2/%d/rerun" % job.id)
        self.assertEqual(resp.status_code, 200)

        # send request to run job with invalid job-id
        resp = self.client.patch("/job/api/v2/%d/rerun" % 9999)
        self.assertEqual(resp.status_code, 404)

        # make and send a job to update entry
        job = Job.new_edit(
            user,
            entry,
            params={
                "attrs": [
                    {
                        "id": str(entry.attrs.first().id),
                        "value": [{"data": "fuga", "index": 0}],
                        "referral_key": [],
                    }
                ]
            },
        )
        resp = self.client.patch("/job/api/v2/%d/rerun" % job.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Job.objects.get(id=job.id).status, JobStatus.DONE)
        self.assertEqual(entry.attrs.first().get_latest_value().value, "fuga")

        # make and send a job to copy entry
        job = Job.new_do_copy(user, entry, params={"new_name": "new_entry"})
        resp = self.client.patch("/job/api/v2/%d/rerun" % job.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Job.objects.get(id=job.id).status, JobStatus.DONE)

        # checks it's success to clone entry
        new_entry = Entry.objects.get(name="new_entry", schema=entity)
        self.assertEqual(new_entry.attrs.first().get_latest_value().value, "fuga")

        # make and send a job to delete entry
        job = Job.new_delete(user, entry)
        resp = self.client.patch("/job/api/v2/%d/rerun" % job.id)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Entry.objects.get(id=entry.id).is_active)

    def test_rerun_deleted_job(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        job = Job.new_create(user, entry)

        # delete target entry
        entry.delete()

        resp = self.client.patch("/job/api/v2/%d/rerun" % job.id)
        self.assertEqual(resp.status_code, 400)

    def test_download_job_with_invalid_param(self):
        user = self.guest_login()

        # send request to download job with invalid job-id
        resp = self.client.get("/job/api/v2/%d/download" % 9999)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"message": "No Job matches the given query.", "code": "AE-230000"}
        )

        # Send a request to a job that cannot be downloaded
        job = Job.new_create(user, None)

        resp = self.client.get("/job/api/v2/%d/download" % job.id)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), [{"message": "Target job cannot be downloaded", "code": "AE-250000"}]
        )

        # send request to download job when job is not done
        job = Job.new_export(user, text="hoge")

        resp = self.client.get("/job/api/v2/%d/download" % job.id)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), [{"message": "Target job has not yet done", "code": "AE-270000"}]
        )

        # send request to download job when not exists file
        job.status = JobStatus.DONE
        job.save()

        resp = self.client.get("/job/api/v2/%d/download" % job.id)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), [{"message": "Target file is not exists", "code": "AE-280000"}]
        )

        # send request to download job
        job.set_cache("日本語")

        resp = self.client.get("/job/api/v2/%d/download" % job.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Disposition"], 'attachment; filename="hoge"')
        self.assertEqual(resp.content.decode("utf-8"), "日本語")

        # send request to download job with utf-8 param
        resp = self.client.get("/job/api/v2/%d/download?encode=utf-8" % job.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode("utf-8"), "日本語")

        # send request to download job with shift_jis param
        resp = self.client.get("/job/api/v2/%d/download?encode=shift_jis" % job.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode("shift_jis"), "日本語")

        # send request to download job with invalid encoding param
        resp = self.client.get("/job/api/v2/%d/download?encode=hoge" % job.id)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), [{"message": "Invalid encode parameter", "code": "AE-250000"}]
        )

        # send request to download job with different user
        self.admin_login()
        resp = self.client.get("/job/api/v2/%d/download" % job.id)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"message": "No Job matches the given query.", "code": "AE-230000"}
        )
