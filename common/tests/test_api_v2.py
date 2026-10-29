from pathlib import Path
from unittest.mock import Mock, patch

import yaml

from airone.lib.test import AironeViewTest
from entity.models import Entity
from group.models import Group
from job import tasks as job_tasks
from job.models import Job, JobOperation, JobStatus
from role import tasks as role_tasks
from role.models import Role
from user.models import User

ENTITY_FIXTURE = Path(__file__).parents[2] / "entity" / "tests" / "fixtures" / "entity.yaml"

PATCH_GENERAL = patch("job.tasks.import_general.delay", Mock(side_effect=job_tasks.import_general))
PATCH_ROLE = patch("role.tasks.import_role_v2.delay", Mock(side_effect=role_tasks.import_role_v2))


class CommonImportAPITest(AironeViewTest):
    def _post(self, data: object, query: str = "") -> object:
        return self.client.post(
            "/common/api/v2/import" + query, yaml.dump(data), content_type="application/yaml"
        )

    def _assert_no_job(self) -> None:
        self.assertFalse(Job.objects.exists())

    @PATCH_GENERAL
    def test_import_entity(self) -> None:
        self.admin_login()
        with open(ENTITY_FIXTURE) as fp:
            data = yaml.safe_load(fp)

        resp = self._post(data)

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["type"], "entity")
        self.assertEqual(len(body["job_ids"]), 1)
        job = Job.objects.get(id=body["job_ids"][0])
        self.assertEqual(job.operation, JobOperation.IMPORT_GENERAL_V2)
        self.assertEqual(job.status, JobStatus.DONE)
        self.assertTrue(Entity.objects.filter(name="entity", is_active=True).exists())

    @PATCH_GENERAL
    def test_import_user(self) -> None:
        self.admin_login()
        Group.objects.create(name="Group1")

        resp = self._post([{"username": "User1", "email": "u1@example.com", "groups": "Group1"}])

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["type"], "user")
        user = User.objects.get(username="User1")
        self.assertEqual(user.email, "u1@example.com")
        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["Group1"])

    @PATCH_GENERAL
    def test_import_user_with_missing_group_makes_the_job_fail(self) -> None:
        self.admin_login()

        resp = self._post([{"username": "User1", "email": "u1@example.com", "groups": "Nope"}])

        self.assertEqual(resp.status_code, 200)
        job = Job.objects.get(id=resp.json()["job_ids"][0])
        self.assertEqual(job.status, JobStatus.ERROR)

    @PATCH_GENERAL
    def test_import_group(self) -> None:
        self.admin_login()

        resp = self._post([{"name": "Group1"}])

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["type"], "group")
        self.assertTrue(Group.objects.filter(name="Group1").exists())

    @PATCH_ROLE
    def test_import_role(self) -> None:
        self.admin_login()

        resp = self._post(
            [
                {
                    "name": "role1",
                    "description": "",
                    "users": [],
                    "groups": [],
                    "admin_users": [],
                    "admin_groups": [],
                    "permissions": [],
                }
            ]
        )

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["type"], "role")
        self.assertEqual(
            Job.objects.get(id=body["job_ids"][0]).operation, JobOperation.IMPORT_ROLE_V2
        )
        self.assertTrue(Role.objects.filter(name="role1").exists())

    def test_import_entry_starts_a_job_per_model(self) -> None:
        user = self.admin_login()
        entity = Entity.objects.create(name="E1", created_user=user)

        with patch("job.models.Job.run", Mock()):
            resp = self._post([{"entity": "E1", "entries": [{"name": "a"}]}])

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["type"], "entry")
        self.assertEqual(body["error"], [])
        job = Job.objects.get(id=body["job_ids"][0])
        self.assertEqual(job.operation, JobOperation.IMPORT_ENTRY_V2)
        self.assertEqual(job.target_id, entity.id)

    def test_import_entry_reports_unknown_model(self) -> None:
        self.admin_login()

        resp = self._post([{"entity": "Nope", "entries": []}])

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["job_ids"], [])
        self.assertEqual(len(resp.json()["error"]), 1)
        self._assert_no_job()

    def test_unrecognized_documents_are_rejected_without_a_job(self) -> None:
        self.admin_login()
        cases = [
            [],
            {},
            {"foo": "bar"},
            [{"unknown": 1}],
            [{"name": "g"}, {"username": "u", "email": "e", "groups": ""}],
            # detected as users, but a user needs its email
            [{"username": "u", "groups": ""}],
            # detected as roles, but a role needs its members
            [{"name": "r", "users": []}],
            # detected as a model file, but the body is not valid
            {"Entity": "x", "EntityAttr": []},
        ]
        for data in cases:
            with self.subTest(data=data):
                resp = self._post(data)
                self.assertEqual(resp.status_code, 400)
                self._assert_no_job()

    def test_unparsable_body_is_rejected_without_a_job(self) -> None:
        self.admin_login()

        resp = self.client.post(
            "/common/api/v2/import", "a: [unclosed", content_type="application/yaml"
        )

        self.assertEqual(resp.status_code, 400)
        self._assert_no_job()

    def test_non_superuser_cannot_import_user_group_role(self) -> None:
        self.guest_login()
        cases = [
            [{"username": "u", "email": "e@example.com", "groups": ""}],
            [{"name": "g"}],
            [
                {
                    "name": "r",
                    "users": [],
                    "groups": [],
                    "admin_users": [],
                    "admin_groups": [],
                }
            ],
        ]
        for data in cases:
            with self.subTest(data=data):
                self.assertEqual(self._post(data).status_code, 403)
                self._assert_no_job()

    def test_readonly_user_cannot_import_models_or_items(self) -> None:
        user = self.guest_login()
        user.is_readonly = True
        user.save()

        for data in ({"Entity": [], "EntityAttr": []}, [{"entity": "E", "entries": []}]):
            with self.subTest(data=data):
                self.assertEqual(self._post(data).status_code, 403)
                self._assert_no_job()

    def test_unauthenticated_request_is_rejected(self) -> None:
        resp = self._post([{"name": "g"}])

        self.assertIn(resp.status_code, (401, 403))
        self._assert_no_job()
