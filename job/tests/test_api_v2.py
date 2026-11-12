import csv
import io
import json
from datetime import timedelta
from unittest.mock import Mock, patch

from django.core.files.storage import default_storage
from django.utils import timezone

from airone.lib.test import AironeViewTest
from entity.models import Entity
from entry import tasks
from entry.models import Entry
from job.models import Job, JobOperation, JobStatus
from role.models import Role

# constants using this tests
_TEST_MAX_LIST_VIEW = 2


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

    def tearDown(self):
        super(ViewTest, self).tearDown()

    def test_export_search_results_as_downloadable_job(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        message = "Failure in entity 日本語\n" + "full traceback\n" * 100
        matched = Job.new_create(
            user, entry, message, params={"entry_name": entry.name, "attrs": []}
        )
        matched.update(JobStatus.ERROR)
        Job.new_create(user, entry, "success", params={"entry_name": entry.name, "attrs": []})
        from user.models import User

        other = User.objects.create(username="other", password="passwd")
        other_job = Job.new_create(
            other, entry, message, params={"entry_name": entry.name, "attrs": []}
        )
        other_job.update(JobStatus.ERROR)
        query = {"status": str(JobStatus.ERROR), "text": "ENTITY", "all_users": "true"}
        with patch.object(Job, "run") as enqueue:
            response = self.client.post("/job/api/v2/jobs", query_params=query)
        self.assertEqual(response.status_code, 202)
        enqueue.assert_called_once_with()
        export = Job.objects.get(id=response.json()["id"])
        self.assertEqual(export.operation, JobOperation.EXPORT_JOB_HISTORY)
        self.assertEqual(export.status, JobStatus.PREPARING)
        self.assertEqual(export.text, f"job_history_{export.id}.csv")
        download_url = f"/job/api/v2/{export.id}/download"
        self.assertEqual(self.client.get(download_url).status_code, 400)
        export.run(will_delay=False)
        export.refresh_from_db()
        self.assertEqual(export.status, JobStatus.DONE)
        with default_storage.open(export.text, "rb") as file:
            rows = list(csv.DictReader(io.StringIO(file.read().decode("utf-8-sig"))))
        self.assertEqual([row["job_id"] for row in rows], [str(matched.id)])
        self.assertEqual(rows[0]["message"], message)
        self.assertEqual(rows[0]["target_entity"], entity.name)
        self.assertEqual(rows[0]["target_entry"], entry.name)
        download = self.client.get(download_url)
        self.assertEqual(download.status_code, 200)
        self.assertIn(export.text, download["Content-Disposition"])
        self.assertEqual(
            list(csv.DictReader(io.StringIO(download.content.decode("utf-8"))))[0]["message"],
            message,
        )
        self.assertEqual(
            list(
                csv.DictReader(
                    io.StringIO(
                        self.client.get(download_url, {"encode": "shift_jis"}).content.decode(
                            "shift_jis"
                        )
                    )
                )
            )[0]["message"],
            message,
        )

        self.admin_login()
        self.assertEqual(self.client.get(download_url).status_code, 403)
        with patch.object(Job, "run"):
            response = self.client.post("/job/api/v2/jobs", query_params=query)
        admin_export = Job.objects.get(id=response.json()["id"])
        admin_export.run(will_delay=False)
        with default_storage.open(admin_export.text, "rb") as file:
            rows = list(csv.DictReader(io.StringIO(file.read().decode("utf-8-sig"))))
        self.assertEqual({row["job_id"] for row in rows}, {str(matched.id), str(other_job.id)})

    def test_export_rejects_invalid_search_without_creating_job(self):
        self.guest_login()
        before = Job.objects.count()
        response = self.client.post("/job/api/v2/jobs", query_params={"created_after": "invalid"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Job.objects.count(), before)

    def test_legacy_history_export_does_not_break_role_job_list(self):
        user = self.guest_login()
        role = Role.objects.create(name="role")
        role_job = Job.new_role_change(user, role.pk, JobOperation.EDIT_ROLE, {}, text="edit")
        legacy = Job.objects.create(
            user=user,
            operation=36,
            status=JobStatus.DONE,
            text="temporary",
            params=json.dumps({"filters": {"status": "3"}}),
        )
        legacy.text = f"job_history_{legacy.id}.csv"
        legacy.save(update_fields=["text"])

        response = self.client.get("/job/api/v2/jobs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 2)
        self.assertEqual(
            response.json()["results"][0]["operation"], JobOperation.EXPORT_JOB_HISTORY
        )
        self.assertIsNone(response.json()["results"][0]["target"])
        self.assertEqual(legacy.operation, JobOperation.EDIT_ROLE)
        self.assertEqual(role_job.operation, JobOperation.EDIT_ROLE)
        filtered = self.client.get(
            "/job/api/v2/jobs", {"operation": JobOperation.EXPORT_JOB_HISTORY}
        )
        self.assertEqual([row["id"] for row in filtered.json()["results"]], [legacy.id])
        with patch(
            "job.api_v2.views.default_storage.open",
            return_value=io.BytesIO(b"job_id,message\n1,error\n"),
        ):
            download = self.client.get(f"/job/api/v2/{legacy.id}/download")
        self.assertEqual(download.status_code, 200)
        self.assertIn(b"job_id,message", download.content)
        self.assertEqual(self.client.get(f"/job/api/v2/{role_job.id}/download").status_code, 400)

    def test_get_jobs(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)

        # create three jobs
        [
            Job.new_create(user, entry, params={"entry_name": entry.name, "attrs": []})
            for _ in range(0, _TEST_MAX_LIST_VIEW)
        ]
        self.assertEqual(Job.objects.filter(user=user).count(), _TEST_MAX_LIST_VIEW)

        # checks number of the returned objects are as expected
        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], _TEST_MAX_LIST_VIEW)

        # admin sees only own jobs by default (same as regular users)
        self.admin_login()
        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 0)

        # admin with all_users=true sees all users' jobs
        resp = self.client.get(
            f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0&all_users=true"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], _TEST_MAX_LIST_VIEW)
        # user field is present in results
        self.assertIn("user", resp.json()["results"][0])

    def test_search_jobs_combines_filters_before_pagination(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        match = Job.new_create(
            user,
            entry,
            "Connection refused by INTERNAL host",
            params={"entry_name": entry.name, "attrs": []},
        )
        match.update(JobStatus.ERROR)
        other = Job.new_create(
            user, entry, "Successful request", params={"entry_name": entry.name, "attrs": []}
        )
        other.update(JobStatus.DONE)

        after = (match.created_at - timedelta(minutes=1)).isoformat()
        before = (match.created_at + timedelta(minutes=1)).isoformat()
        for key, value in (
            ("job_id", match.id),
            ("status", JobStatus.ERROR),
            ("operation", JobOperation.CREATE_ENTRY),
            ("user", user.username.upper()[:3]),
            ("text", "internal"),
            ("created_after", after),
            ("created_before", before),
        ):
            self.assertIn(
                match.id,
                [
                    job["id"]
                    for job in self.client.get("/job/api/v2/jobs", {key: value}).json()["results"]
                ],
                key,
            )
        resp = self.client.get(
            "/job/api/v2/jobs",
            {
                "limit": 1,
                "offset": 0,
                "job_id": match.id,
                "status": JobStatus.ERROR,
                "operation": JobOperation.CREATE_ENTRY,
                "user": user.username.upper()[:3],
                "text": "internal",
                "created_after": after,
                "created_before": before,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()["results"][0]["id"], match.id)
        self.assertEqual(
            self.client.get("/job/api/v2/jobs", {"text": "successful"}).json()["count"], 1
        )
        self.assertEqual(
            self.client.get(
                "/job/api/v2/jobs", {"status": JobStatus.ERROR, "text": "successful"}
            ).json()["count"],
            0,
        )

    def test_search_jobs_excludes_internal_and_deleted_targets(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        visible = Job.new_create(
            user, entry, "visible", params={"entry_name": entry.name, "attrs": []}
        )
        Job.objects.create(
            user=user,
            target=entry,
            operation=JobOperation.UPDATE_DOCUMENT,
            status=JobStatus.ERROR,
            text="hidden internal error",
            params="{}",
        )
        deleted_entry = Entry.objects.create(
            name="deleted entry", created_user=user, schema=entity, is_active=False
        )
        Job.new_create(
            user,
            deleted_entry,
            "deleted target",
            params={"entry_name": deleted_entry.name, "attrs": []},
        )
        Job.objects.create(
            user=user,
            target=deleted_entry,
            operation=JobOperation.DELETE_ENTRY,
            status=JobStatus.DONE,
            text="delete operation",
            params="{}",
        )

        for params in ({}, {"include_hidden": "true", "include_empty_success": "true"}):
            with self.subTest(params=params):
                resp = self.client.get("/job/api/v2/jobs", params)
                self.assertEqual([job["id"] for job in resp.json()["results"]], [visible.id])

        self.admin_login()
        for params in (
            {"all_users": "true"},
            {"all_users": "true", "include_hidden": "true", "include_empty_success": "true"},
        ):
            with self.subTest(params=params):
                resp = self.client.get("/job/api/v2/jobs", params)
                self.assertEqual([job["id"] for job in resp.json()["results"]], [visible.id])

        self.assertEqual(
            self.client.get("/job/api/v2/jobs", {"all_users": "true", "text": "internal"}).json()[
                "count"
            ],
            0,
        )

    def test_search_jobs_matches_multiple_operation_ids(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        created_entry = Job.new_create(user, entry, params={"entry_name": entry.name, "attrs": []})
        created_entity = Job.objects.create(
            user=user,
            target=entity,
            operation=JobOperation.CREATE_ENTITY,
            status=JobStatus.DONE,
            text="created entity",
            params="{}",
        )
        Job.objects.create(
            user=user,
            target=entry,
            operation=JobOperation.EDIT_ENTRY,
            status=JobStatus.DONE,
            text="edited entry",
            params="{}",
        )

        resp = self.client.get(
            "/job/api/v2/jobs",
            {"operation": f"{JobOperation.CREATE_ENTRY},{JobOperation.CREATE_ENTITY}"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            {job["id"] for job in resp.json()["results"]},
            {created_entry.id, created_entity.id},
        )

    def test_search_jobs_rejects_invalid_filters(self):
        self.guest_login()
        for params in (
            {"status": "oops"},
            {"job_id": "-1"},
            {"operation": "1,invalid"},
            {"operation": "1,-2"},
            {"created_before": "invalid"},
            {"created_before": "2026-02-30T00:00:00"},
        ):
            with self.subTest(params=params):
                self.assertEqual(self.client.get("/job/api/v2/jobs", params).status_code, 400)

    def test_expired_job_is_reported_as_timeout_without_changing_terminal_status(self):
        user = self.guest_login()
        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        job = Job.new_create(user, entry, params={"entry_name": entry.name, "attrs": []})
        Job.objects.filter(id=job.id).update(updated_at=timezone.now() - timedelta(minutes=10))

        with patch.object(Job, "_get_job_timeout", return_value=60):
            response = self.client.get(f"/job/api/v2/jobs?target_id={entry.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["status"], JobStatus.TIMEOUT)
        with patch.object(Job, "_get_job_timeout", return_value=60):
            self.assertEqual(
                self.client.get("/job/api/v2/jobs", {"status": JobStatus.TIMEOUT}).json()["count"],
                1,
            )
            self.assertEqual(
                self.client.get("/job/api/v2/jobs", {"status": JobStatus.PREPARING}).json()[
                    "count"
                ],
                0,
            )
        with patch.object(Job, "_get_job_timeout", return_value=60):
            detail = self.client.get(f"/job/api/v2/{job.id}/")
        self.assertEqual(detail.json()["status"], JobStatus.TIMEOUT)
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.PREPARING)

        job.update(JobStatus.PROCESSING)
        Job.objects.filter(id=job.id).update(updated_at=timezone.now() - timedelta(minutes=10))
        with patch.object(Job, "_get_job_timeout", return_value=60):
            response = self.client.get(f"/job/api/v2/jobs?target_id={entry.id}")
        self.assertEqual(response.json()["results"][0]["status"], JobStatus.TIMEOUT)

        job.update(JobStatus.DONE)
        Job.objects.filter(id=job.id).update(updated_at=timezone.now() - timedelta(minutes=10))
        with patch.object(Job, "_get_job_timeout", return_value=60):
            response = self.client.get(f"/job/api/v2/jobs?target_id={entry.id}")
        self.assertEqual(response.json()["results"][0]["status"], JobStatus.DONE)

    def test_get_jobs_includes_role_import_without_target(self):
        user = self.guest_login()
        Job.new_role_import_v2(
            user,
            params=[
                {
                    "name": "role",
                    "description": "",
                    "users": [],
                    "groups": [],
                    "admin_users": [user.username],
                    "admin_groups": [],
                    "permissions": [],
                }
            ],
        )

        resp = self.client.get("/job/api/v2/jobs?limit=100&offset=0")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()["results"][0]["operation"], JobOperation.IMPORT_ROLE_V2)

    def test_get_jobs_includes_role_changes_without_acl_target(self):
        user = self.guest_login()
        role = Role.objects.create(name="role")
        jobs = []
        for operation, status in (
            (JobOperation.EDIT_ROLE, JobStatus.PREPARING),
            (JobOperation.DELETE_ROLE, JobStatus.DONE),
            (JobOperation.RESTORE_ROLE, JobStatus.ERROR),
        ):
            job = Job.new_role_change(user, role.pk, operation, {}, text="Role change")
            job.update(status)
            jobs.append(job)

        response = self.client.get("/job/api/v2/jobs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], len(jobs))
        self.assertEqual(
            [row["id"] for row in response.json()["results"]],
            [job.pk for job in reversed(jobs)],
        )
        for row in response.json()["results"]:
            self.assertEqual(row["target"]["id"], role.pk)
            self.assertEqual(row["target"]["name"], role.name)

        # Deleting a role must not hide the audit trail of its changes.
        role.is_active = False
        role.save()
        response = self.client.get("/job/api/v2/jobs", {"operation": JobOperation.DELETE_ROLE})
        self.assertEqual([row["id"] for row in response.json()["results"]], [jobs[1].pk])

        # Role jobs retain the same user scoping as other jobs.
        self.admin_login()
        self.assertEqual(self.client.get("/job/api/v2/jobs").json()["count"], 0)
        response = self.client.get("/job/api/v2/jobs", {"all_users": "true"})
        self.assertEqual(response.json()["count"], len(jobs))

    def test_get_jobs_deleted_target(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        Job.new_create(user, entry, params={"entry_name": entry.name, "attrs": []})

        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 1)

        # Jobs for deleted targets are omitted from the list.
        entry.delete()

        # Create delete job
        Job.new_delete(user, entry)

        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertEqual(body["count"], 0)

    def test_get_jobs_deleted_target_v2_entry(self):
        """DELETE_ENTRY_V2 jobs for inactive targets are omitted from the list."""
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)

        # Create delete job v2 and mark entry as deleted (is_active=False)
        entry.is_active = False
        entry.save()
        Job.new_delete_entry_v2(user, entry)

        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertEqual(body["count"], 0)

    def test_get_jobs_deleted_target_v2_entity(self):
        """DELETE_ENTITY_V2 jobs for inactive targets are omitted from the list."""
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)

        # Create delete job v2 and mark entity as deleted (is_active=False)
        entity.is_active = False
        entity.save()
        Job.new_delete_entity_v2(user, entity)

        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertEqual(body["count"], 0)

    @patch("entry.tasks.create_entry_v2.delay", Mock(side_effect=tasks.create_entry_v2))
    def test_create_entry_v2_job_is_listed(self):
        """Item creation from the new UI (api_v2) should appear in the job list.

        Expected behaviour: creating an entry through POST
        /entity/api/v2/<entity_id>/entries/ generates a CREATE_ENTRY_V2 job
        that the user can see in the job list (just like edit/delete jobs).
        """
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)

        # create an entry through the new UI (api_v2) endpoint
        params = {"name": "new_entry", "schema": entity.id, "attrs": []}
        resp = self.client.post(
            "/entity/api/v2/%d/entries/" % entity.id,
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 202, resp.content)

        # the entry must have been created (the task ran synchronously)
        created = Entry.objects.filter(name="new_entry", schema=entity).first()
        self.assertIsNotNone(created)

        # the CREATE_ENTRY_V2 job must be visible in the job list
        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        operations = [r["operation"] for r in body["results"]]
        self.assertIn(
            JobOperation.CREATE_ENTRY_V2,
            operations,
            "CREATE_ENTRY_V2 job should be listed but was not: %s" % operations,
        )

    def test_get_non_target_job(self):
        user = self.guest_login()

        Job.new_create(user, None, params={"entry_name": "synthetic-entry", "attrs": []})

        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 0)

    def test_get_exporting_job(self):
        user = self.guest_login()
        Job.new_export_configuration_v2(user, "entity")

        # create jobs which are related with export
        (Job.new_export(user, params={"export_format": "yaml", "target_id": 0}),)
        (
            Job.new_export_search_result(
                user,
                params={"entities": [], "attrinfo": [], "export_style": "yaml"},
            ),
        )

        resp = self.client.get(f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 3)

    def test_get_recent_job(self):
        user = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=user)
        entry = Entry.objects.create(name="entry", created_user=user, schema=entity)
        job = Job.new_create(user, entry, "hoge", params={"entry_name": entry.name, "attrs": []})

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
        [
            Job.new_create(user, entry1, params={"entry_name": entry1.name, "attrs": []})
            for _ in range(0, _TEST_MAX_LIST_VIEW)
        ]
        self.assertEqual(Job.objects.filter(user=user).count(), _TEST_MAX_LIST_VIEW)
        # create one job for entry2
        Job.new_create(user, entry2, params={"entry_name": entry2.name, "attrs": []})

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
        job = Job.new_create(user, entry, "hoge", params={"entry_name": entry.name, "attrs": []})

        resp = self.client.get("/job/api/v2/%d/" % job.id)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["id"], job.id)
        self.assertEqual(body["status"], JobStatus.PREPARING)
        self.assertEqual(body["text"], "hoge")

    def test_get_job_with_invalid_param(self):
        self.guest_login()
        resp = self.client.get("/job/api/v2/%d/" % 9999)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"code": "AE-230000", "message": "No Job matches the given query."}
        )

    def test_admin_get_other_users_job(self):
        guest = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=guest)
        entry = Entry.objects.create(name="entry", created_user=guest, schema=entity)
        job = Job.new_create(guest, entry, "hoge", params={"entry_name": entry.name, "attrs": []})

        self.admin_login()

        # admin can retrieve any job by ID without extra parameters
        resp = self.client.get("/job/api/v2/%d/" % job.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], job.id)
        self.assertEqual(resp.json()["user"], guest.username)

        # admin cannot cancel another user's job
        resp = self.client.delete("/job/api/v2/%d/" % job.id)
        self.assertEqual(resp.status_code, 403)

    def test_non_admin_cannot_use_all_users(self):
        guest = self.guest_login()

        entity = Entity.objects.create(name="entity", created_user=guest)
        entry = Entry.objects.create(name="entry", created_user=guest, schema=entity)
        Job.new_create(guest, entry, params={"entry_name": entry.name, "attrs": []})

        from user.models import User

        other = User.objects.create(username="other", password="passwd", is_superuser=False)
        other_job = Job.new_create(other, entry, params={"entry_name": entry.name, "attrs": []})

        # all_users=true is silently ignored for non-admin; only own jobs are returned
        resp = self.client.get(
            f"/job/api/v2/jobs?limit={_TEST_MAX_LIST_VIEW + 100}&offset=0&all_users=true"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 1)

        # non-admin cannot retrieve another user's job by ID
        resp = self.client.get("/job/api/v2/%d/" % other_job.id)
        self.assertEqual(resp.status_code, 404)

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
        job = Job.new_create(user, entry, params={"entry_name": entry.name, "attrs": []})
        self.assertEqual(job.status, JobStatus.PREPARING)
        resp = self.client.delete("/job/api/v2/%d/" % job.id)
        self.assertEqual(resp.status_code, 204)

    def test_download_job_with_invalid_param(self):
        user = self.guest_login()

        # send request to download job with invalid job-id
        resp = self.client.get("/job/api/v2/%d/download" % 9999)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"message": "No Job matches the given query.", "code": "AE-230000"}
        )

        # Send a request to a job that cannot be downloaded
        job = Job.new_create(user, None, params={"entry_name": "synthetic-entry", "attrs": []})

        resp = self.client.get("/job/api/v2/%d/download" % job.id)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), [{"message": "Target job cannot be downloaded", "code": "AE-250000"}]
        )

        # send request to download job when job is not done
        job = Job.new_export(user, text="hoge", params={"export_format": "yaml", "target_id": 0})

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

        # send request to download job with different user (superuser can retrieve but not download)
        self.admin_login()
        resp = self.client.get("/job/api/v2/%d/download" % job.id)
        self.assertEqual(resp.status_code, 403)
