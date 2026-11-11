import json
from unittest.mock import patch

from airone.lib.test import AironeViewTest
from group.models import Group
from job.api_v2.serializers import JobSerializers
from job.models import Job, JobOperation, JobStatus
from role.history import role_history_events
from role.models import HistoricalPermission, Role
from user.models import User


class RoleHistoryTest(AironeViewTest):
    def setUp(self):
        super().setUp()
        self.admin = self.admin_login()
        self.member = User.objects.create(username="member")
        self.role = Role.objects.create(name="original", description="before")
        self.role.admin_users.add(self.admin)
        self.role.users.add(self.member)
        self.original = self.role.history.first()

    def data(self, **changes):
        return {
            "name": "changed",
            "description": "after",
            "users": [],
            "groups": [],
            "admin_users": [self.admin.pk],
            "admin_groups": [],
            **changes,
        }

    def update(self):
        response = self.client.put(
            f"/role/api/v2/{self.role.pk}", json.dumps(self.data()), "application/json"
        )
        self.assertEqual(response.status_code, 202)
        job = Job.objects.get(pk=response.json()["job_id"])
        job.run(will_delay=False)
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.DONE)
        return job

    def test_worker_records_actor_members_and_job(self):
        job = self.update()
        history = self.role.history.first()
        self.assertEqual(history.name, "changed")
        self.assertEqual(history.history_user, self.admin)
        self.assertEqual(list(history.users.all()), [])
        self.assertIn(str(job.pk), history.history_change_reason)
        self.assertEqual(JobSerializers(job).data["target"]["id"], self.role.pk)
        jobs = self.client.get("/job/api/v2/jobs").json()["results"]
        self.assertIn(job.pk, [row["id"] for row in jobs])

        response = self.client.get(f"/role/api/v2/{self.role.pk}/histories/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["history_id"], history.history_id)

    def test_restore_is_audited_and_restores_members(self):
        self.update()
        response = self.client.post(
            f"/role/api/v2/{self.role.pk}/restore/", {"history_id": self.original.history_id}
        )
        self.assertEqual(response.status_code, 202)
        job = Job.objects.get(pk=response.json()["job_id"])
        job.run(will_delay=False)
        self.role.refresh_from_db()
        self.assertEqual(self.role.name, "original")
        self.assertEqual(self.role.description, "before")
        self.assertEqual(list(self.role.users.all()), [self.member])
        self.assertIn("restored history", self.role.history.first().history_change_reason)
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.DONE)

    def test_cannot_restore_another_roles_history(self):
        other = Role.objects.create(name="other")
        response = self.client.post(
            f"/role/api/v2/{self.role.pk}/restore/",
            {"history_id": other.history.first().history_id},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Job.objects.filter(operation=JobOperation.RESTORE_ROLE).exists())

    def test_worker_rechecks_permission(self):
        self.admin.is_superuser = False
        self.admin.save()
        response = self.client.put(
            f"/role/api/v2/{self.role.pk}", json.dumps(self.data()), "application/json"
        )
        self.assertEqual(response.status_code, 202)
        self.role.admin_users.clear()
        job = Job.objects.get(pk=response.json()["job_id"])
        job.run(will_delay=False)
        job.refresh_from_db()
        self.role.refresh_from_db()
        self.assertEqual(job.status, JobStatus.ERROR)
        self.assertEqual(self.role.name, "original")

    def test_failed_change_is_atomic(self):
        job = Job.new_role_change(
            self.admin, self.role.pk, JobOperation.EDIT_ROLE, {"data": self.data()}
        )
        count = self.role.history.count()
        original_save = Role.save

        def fail_final_snapshot(instance, *args, **kwargs):
            if hasattr(instance, "skip_history_when_saving"):
                return original_save(instance, *args, **kwargs)
            raise RuntimeError("failed")

        with patch("role.models.Role.save", autospec=True, side_effect=fail_final_snapshot):
            job.run(will_delay=False)
        self.role.refresh_from_db()
        self.assertEqual(self.role.name, "original")
        self.assertEqual(list(self.role.users.all()), [self.member])
        self.assertEqual(self.role.history.count(), count)

    def test_acl_changes_and_restore_permissions(self):
        entity = self.create_entity(self.admin, "entity")
        permission = entity.readable
        permission._history_user = self.admin
        permission.roles.add(self.role)
        granted = permission.history.first()
        history_count = self.role.history.count()
        event = role_history_events(self.role)[0]
        self.assertEqual(event["history_source"], "permission")
        self.assertEqual(event["relations"]["permissions"][0]["id"], permission.pk)
        self.assertEqual(event["history_user"], self.admin)
        permission.roles.clear()
        self.assertEqual(self.role.history.count(), history_count)
        self.assertEqual(role_history_events(self.role)[0]["relations"]["permissions"], [])
        response = self.client.post(
            f"/role/api/v2/{self.role.pk}/restore/",
            {"history_id": granted.history_id, "history_source": "permission"},
        )
        self.assertEqual(response.status_code, 202)
        job = Job.objects.get(pk=response.json()["job_id"])
        job.run(will_delay=False)
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.DONE)
        self.assertEqual(list(self.role.permissions.all()), [permission])
        self.assertEqual(permission.history.first().history_user, self.admin)
        self.assertIn("restored history", permission.history.first().history_change_reason)

    def test_readonly_and_unrelated_user_cannot_restore(self):
        self.admin.is_readonly = True
        self.admin.save()
        response = self.client.post(
            f"/role/api/v2/{self.role.pk}/restore/", {"history_id": self.original.history_id}
        )
        self.assertEqual(response.status_code, 403)
        self.guest_login()
        self.assertEqual(
            self.client.get(f"/role/api/v2/{self.role.pk}/histories/").status_code, 403
        )

    def test_existing_role_gets_baseline(self):
        self.role.history.all().delete()
        self.update()
        self.assertEqual(self.role.history.last().name, "original")
        self.assertEqual(self.role.history.last().users.first().user_id, self.member.pk)

    def test_deleted_role_history_remains_accessible_and_can_be_restored(self):
        job = Job.new_role_change(self.admin, self.role.pk, JobOperation.DELETE_ROLE, {})
        job.run(will_delay=False)
        self.role.refresh_from_db()
        self.assertFalse(self.role.is_active)
        response = self.client.get(f"/role/api/v2/{self.role.pk}/histories/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["role"]["is_active"])
        response = self.client.post(
            f"/role/api/v2/{self.role.pk}/restore/", {"history_id": self.original.history_id}
        )
        self.assertEqual(response.status_code, 202)
        job = Job.objects.get(pk=response.json()["job_id"])
        job.run(will_delay=False)
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.DONE)
        self.role.refresh_from_db()
        self.assertTrue(self.role.is_active)
        self.assertEqual(self.role.name, "original")

    def test_role_admin_cannot_restore_permissions_without_full_acl(self):
        entity = self.create_entity(self.admin, "protected", is_public=False)
        permission = entity.full
        permission.roles.add(self.role)
        granted = permission.history.first()
        permission.roles.remove(self.role)
        self.admin.is_superuser = False
        self.admin.save()
        response = self.client.post(
            f"/role/api/v2/{self.role.pk}/restore/",
            {"history_id": granted.history_id, "history_source": "permission"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Job.objects.filter(operation=JobOperation.RESTORE_ROLE).exists())

    def test_reverse_membership_change_is_recorded(self):
        self.member.role.clear()
        self.assertEqual(list(self.role.history.first().users.all()), [])
        self.member.role.add(self.role)
        self.assertEqual(self.role.history.first().users.first().user_id, self.member.pk)

    def test_history_is_paginated_without_changing_role_list_response(self):
        for i in range(12):
            self.role.description = str(i)
            self.role.save()
        response = self.client.get(f"/role/api/v2/{self.role.pk}/histories/?limit=10&offset=10")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json()["count"], 10)
        self.assertLessEqual(len(response.json()["results"]), 10)
        self.assertIsInstance(self.client.get("/role/api/v2/").json(), list)

    def test_update_only_enqueues_until_worker_runs(self):
        before = self.role.history.count()
        with patch("role.tasks.change_role.delay") as send_to_worker:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.put(
                    f"/role/api/v2/{self.role.pk}", json.dumps(self.data()), "application/json"
                )
        self.assertEqual(response.status_code, 202)
        job = Job.objects.get(pk=response.json()["job_id"])
        send_to_worker.assert_called_once_with(job.pk)
        self.role.refresh_from_db()
        self.assertEqual(job.status, JobStatus.PREPARING)
        self.assertEqual(self.role.name, "original")
        self.assertEqual(list(self.role.users.all()), [self.member])
        self.assertEqual(self.role.history.count(), before)
        job.run(will_delay=False)
        self.role.refresh_from_db()
        self.assertEqual(self.role.name, "changed")
        self.assertEqual(self.role.history.count(), before + 1)

    def test_permission_names_are_preserved_when_target_is_renamed(self):
        entity = self.create_entity(self.admin, "original target")
        entity.readable.roles.add(self.role)
        event = role_history_events(self.role)[0]
        entity.name = "renamed target"
        entity.save()
        response = self.client.get(f"/role/api/v2/{self.role.pk}/histories/")
        self.assertEqual(event["relations"]["permissions"][0]["name"], "original target")
        self.assertEqual(
            response.json()["results"][0]["relations"]["permissions"][0]["name"], "original target"
        )

    def test_permission_history_before_role_tracking_reconstructs_initial_permissions(self):
        entity = self.create_entity(self.admin, "existing target")
        self.role.history.all().delete()
        entity.readable.roles.add(self.role)
        self.role.save()
        events = role_history_events(self.role)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["history_source"], "role")
        self.assertEqual(events[0]["relations"]["permissions"][0]["id"], entity.readable.pk)

    def test_permission_changes_for_another_role_are_not_shown(self):
        entity = self.create_entity(self.admin, "shared target")
        permission = entity.readable
        permission.roles.add(self.role)
        count = len(role_history_events(self.role))
        another = Role.objects.create(name="another")
        permission.roles.add(another)
        permission.roles.remove(another)
        self.assertEqual(len(role_history_events(self.role)), count)

    def test_cannot_restore_permission_history_of_another_role(self):
        another = Role.objects.create(name="another")
        permission = self.create_entity(self.admin, "target").readable
        permission.roles.add(another)
        response = self.client.post(
            f"/role/api/v2/{self.role.pk}/restore/",
            {"history_id": permission.history.first().history_id, "history_source": "permission"},
        )
        self.assertEqual(response.status_code, 400)

    def test_json_snapshot_field_is_not_used(self):
        self.assertNotIn("relations", [field.name for field in Role.history.model._meta.fields])
        self.assertEqual(HistoricalPermission.history.model.roles.model.objects.count(), 0)

    def test_restores_all_four_native_membership_relations(self):
        member_group = Group.objects.create(name="members")
        admin_group = Group.objects.create(name="administrators")
        self.role.groups.add(member_group)
        self.role.admin_groups.add(admin_group)
        original = self.role.history.first()
        self.update()
        response = self.client.post(
            f"/role/api/v2/{self.role.pk}/restore/", {"history_id": original.history_id}
        )
        self.assertEqual(response.status_code, 202)
        job = Job.objects.get(pk=response.json()["job_id"])
        job.run(will_delay=False)
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.DONE)
        self.assertEqual(list(self.role.users.all()), [self.member])
        self.assertEqual(list(self.role.admin_users.all()), [self.admin])
        self.assertEqual(list(self.role.groups.all()), [member_group])
        self.assertEqual(list(self.role.admin_groups.all()), [admin_group])

    def test_role_history_restore_uses_permission_state_at_that_time(self):
        permission = self.create_entity(self.admin, "target").readable
        permission.roles.add(self.role)
        self.update()
        original = self.role.history.first()
        permission.roles.remove(self.role)
        response = self.client.post(
            f"/role/api/v2/{self.role.pk}/restore/", {"history_id": original.history_id}
        )
        self.assertEqual(response.status_code, 202)
        Job.objects.get(pk=response.json()["job_id"]).run(will_delay=False)
        self.assertEqual(list(self.role.permissions.all()), [permission])

    def test_permission_restore_uses_membership_state_at_that_time(self):
        permission = self.create_entity(self.admin, "target").readable
        permission.roles.add(self.role)
        original = permission.history.first()
        self.update()
        response = self.client.post(
            f"/role/api/v2/{self.role.pk}/restore/",
            {"history_id": original.history_id, "history_source": "permission"},
        )
        self.assertEqual(response.status_code, 202)
        Job.objects.get(pk=response.json()["job_id"]).run(will_delay=False)
        self.role.refresh_from_db()
        self.assertEqual(self.role.name, "original")
        self.assertEqual(list(self.role.users.all()), [self.member])
