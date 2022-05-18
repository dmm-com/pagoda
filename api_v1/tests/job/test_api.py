import json

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrTypeValue
from datetime import timedelta

from job.models import Job, JobOperation
from entry.models import Entry
from entity.models import Entity, EntityAttr

from job.settings import CONFIG

# constants using this tests
_TEST_MAX_LIST_NAV = 3


class APITest(AironeViewTest):
    def setUp(self):
        super(APITest, self).setUp()

        # save original configuration not to make affect other tests by chaning this
        self.old_config = CONFIG.conf

        CONFIG.conf["MAX_LIST_NAV"] = _TEST_MAX_LIST_NAV

    def tearDown(self):
        super(APITest, self).tearDown()

        # retrieve original configuration for Job.settings.CONFIG
        CONFIG.conf = self.old_config

    def test_get_jobs(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)

        # create three jobs
        jobs = [Job.new_create(user, entry) for _ in range(0, 3)]

        resp = self.client.get("/api/v1/job/")
        self.assertEqual(resp.status_code, 200)

        # checks expected parameters are set correctly
        results = resp.json()
        self.assertEqual(
            results["constant"]["operation"],
            {
                "create": JobOperation.CREATE_ENTRY.value,
                "edit": JobOperation.EDIT_ENTRY.value,
                "delete": JobOperation.DELETE_ENTRY.value,
                "copy": JobOperation.COPY_ENTRY.value,
                "do_copy": JobOperation.DO_COPY_ENTRY.value,
                "import": JobOperation.IMPORT_ENTRY.value,
                "export": JobOperation.EXPORT_ENTRY.value,
                "export_search_result": JobOperation.EXPORT_SEARCH_RESULT.value,
                "restore": JobOperation.RESTORE_ENTRY.value,
                "create_entity": JobOperation.CREATE_ENTITY.value,
                "edit_entity": JobOperation.EDIT_ENTITY.value,
                "delete_entity": JobOperation.DELETE_ENTITY.value,
            },
        )
        self.assertEqual(
            results["constant"]["status"],
            {
                "processing": Job.STATUS["PROCESSING"],
                "done": Job.STATUS["DONE"],
                "error": Job.STATUS["ERROR"],
                "timeout": Job.STATUS["TIMEOUT"],
            },
        )

        # checks the parameter MAXLIST_NAV is applied
        self.assertEqual(Job.objects.filter(user=user).count(), 3)
        self.assertEqual(len(results["result"]), _TEST_MAX_LIST_NAV)

        # After cheeting created_at time back to CONFIG.RECENT_SECONDS or more,
        # this checks that nothing result will be returned.
        for job in jobs:
            job.created_at = job.created_at - timedelta(seconds=(CONFIG.RECENT_SECONDS + 1))
            job.save(update_fields=["created_at"])

        resp = self.client.get("/api/v1/job/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["result"]), 0)

    def test_rerun_jobs(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        attr = EntityAttr.objects.create(
            name="attr",
            created_user=user,
            type=AttrTypeValue["string"],
            parent_entity=entity,
        )
        entity.attrs.add(attr)

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
        resp = self.client.post("/api/v1/job/run/%d" % job.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'"Success to run command"')

        job = Job.objects.get(id=job.id)
        self.assertEqual(job.status, Job.STATUS["DONE"])
        self.assertEqual(entry.attrs.count(), 1)

        attrv = entry.attrs.first().get_latest_value()
        self.assertEqual(attrv.value, "hoge")

        # send request to run job with finished job-id
        resp = self.client.post("/api/v1/job/run/%d" % job.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'"Target job has already been done"')

        # send request to run job with invalid job-id
        resp = self.client.post("/api/v1/job/run/%d" % 9999)
        self.assertEqual(resp.status_code, 400)

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
        resp = self.client.post("/api/v1/job/run/%d" % job.id)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'"Success to run command"')
        self.assertEqual(Job.objects.get(id=job.id).status, Job.STATUS["DONE"])
        self.assertEqual(entry.attrs.first().get_latest_value().value, "fuga")

        # make and send a job to copy entry
        job = Job.new_do_copy(user, entry, params={"new_name": "new_entry"})
        resp = self.client.post("/api/v1/job/run/%d" % job.id)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'"Success to run command"')
        self.assertEqual(Job.objects.get(id=job.id).status, Job.STATUS["DONE"])

        # checks it's success to clone entry
        new_entry = Entry.objects.get(name="new_entry", schema=entity)
        self.assertEqual(new_entry.attrs.first().get_latest_value().value, "fuga")

        # make and send a job to delete entry
        job = Job.new_delete(user, entry)
        resp = self.client.post("/api/v1/job/run/%d" % job.id)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'"Success to run command"')
        self.assertFalse(Entry.objects.get(id=entry.id).is_active)

    def test_rerun_deleted_job(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        job = Job.new_create(user, entry)

        # delete target entry
        entry.delete()

        resp = self.client.post("/api/v1/job/run/%d" % job.id)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'"Job target has already been deleted"')

    def test_get_search_job(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        # make a job
        job = Job.new_delete(user, entry)

        # send request without any GET parameters
        resp = self.client.get("/api/v1/job/search")
        self.assertEqual(resp.status_code, 400)

        # send request with a GET parameter that doesn't match any job
        resp = self.client.get("/api/v1/job/search", {"operation": JobOperation.COPY_ENTRY.value})
        self.assertEqual(resp.status_code, 404)

        # send requests with GET parameter that matches the created job
        for param in [
            {"operation": JobOperation.DELETE_ENTRY.value},
            {"target_id": entry.id},
        ]:
            resp = self.client.get("/api/v1/job/search", param)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(resp.json()), 1)
            self.assertEqual(resp.json()["result"][0]["id"], job.id)
            self.assertEqual(resp.json()["result"][0]["target"]["id"], entry.id)

    def test_cancel_job(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        # make a job
        job = Job.new_delete(user, entry)
        self.assertEqual(job.status, Job.STATUS["PREPARING"])

        # send request without any parameters
        resp = self.client.delete("/api/v1/job/", json.dumps({}), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'"Parameter job_id is required"')

        # send request with invalid job id
        resp = self.client.delete("/api/v1/job/", json.dumps({"job_id": 99999}), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'"Failed to find Job(id=99999)"')

        # target jobs that cannot be canceled
        resp = self.client.delete(
            "/api/v1/job/", json.dumps({"job_id": job.id}), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'"Target job cannot be canceled"')

        # send request with proper parameter
        job = Job.new_create(user, entry)
        self.assertEqual(job.status, Job.STATUS["PREPARING"])

        resp = self.client.delete(
            "/api/v1/job/", json.dumps({"job_id": job.id}), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'"Success to cancel job"')

        job.refresh_from_db()
        self.assertEqual(job.status, Job.STATUS["CANCELED"])

    def test_hidden_jobs_is_not_shown(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", schema=entity, created_user=user)

        # create a hidden job
        Job.new_register_referrals(user, entry)

        # create an unhidden job
        Job.new_create(user, entry)

        resp = self.client.get("/api/v1/job/")
        self.assertEqual(resp.status_code, 200)

        # check API result doesn't contain hidden job
        resp_data = resp.json()
        self.assertEqual(len(resp_data["result"]), 1)
        self.assertEqual(resp_data["result"][0]["operation"], JobOperation.CREATE_ENTRY.value)
