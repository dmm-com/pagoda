from unittest.mock import patch

from airone.lib.test import AironeViewTest, load_export_payload
from airone.lib.types import AttrType
from common.lib.import_detector import ImportType
from entity.models import Entity, EntityAttr
from job.models import Job, JobStatus
from job.params import ConfigurationExportParams


class ConfigurationExportTest(AironeViewTest):
    def test_export_is_unavailable_until_worker_finishes_and_owner_only(self):
        self.guest_login()
        with patch.object(Job, "run") as enqueue:
            response = self.client.get("/entity/api/v2/export")
        self.assertEqual(response.status_code, 202)
        enqueue.assert_called_once_with()
        job = Job.objects.get(id=response.json()["id"])
        self.assertEqual(job.status, JobStatus.PREPARING)
        jobs = self.client.get("/job/api/v2/jobs").json()["results"]
        self.assertIn(job.id, [item["id"] for item in jobs])
        url = f"/job/api/v2/{job.id}/download"
        self.assertEqual(self.client.get(url).status_code, 400)

        job.run(will_delay=False)
        self.assertEqual(self.client.get(url).status_code, 200)
        jobs = self.client.get("/job/api/v2/jobs").json()["results"]
        self.assertIn(job.id, [item["id"] for item in jobs])

        # Even an administrator cannot download another user's export.
        self.admin_login()
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_worker_filters_unreadable_entities_and_attributes(self):
        user = self.guest_login()
        visible = Entity.objects.create(name="visible", created_user=user)
        Entity.objects.create(name="hidden", created_user=user, is_public=False)
        EntityAttr.objects.create(
            name="hidden-attribute",
            parent_entity=visible,
            created_user=user,
            type=AttrType.STRING,
            is_public=False,
        )
        job = Job.new_export_configuration_v2(user, "entity")
        job.run(will_delay=False)
        data = load_export_payload(job.get_cache(), ImportType.ENTITY)
        self.assertEqual([entity["name"] for entity in data["Entity"]], ["visible"])
        self.assertEqual(data["EntityAttr"], [])

    def test_single_entity_export_api_and_worker_export_only_requested_entity(self):
        user = self.guest_login()
        selected = Entity.objects.create(name="selected", created_user=user)
        other = Entity.objects.create(name="other", created_user=user)
        selected_attr = EntityAttr.objects.create(
            name="selected-attribute",
            parent_entity=selected,
            created_user=user,
            type=AttrType.STRING,
        )
        EntityAttr.objects.create(
            name="other-attribute",
            parent_entity=other,
            created_user=user,
            type=AttrType.STRING,
        )

        # The response serializer is part of this regression: the endpoint must
        # return its accepted job instead of raising a NameError after enqueueing.
        with patch.object(Job, "run") as enqueue:
            response = self.client.get(f"/entity/api/v2/export?entity_id={selected.id}")
        self.assertEqual(response.status_code, 202, response.content)
        enqueue.assert_called_once_with()

        job = Job.objects.get(id=response.json()["id"])
        params = job.get_typed_params(ConfigurationExportParams)
        self.assertEqual(params.entity_id, selected.id)
        job.run(will_delay=False)

        data = yaml.safe_load(job.get_cache())
        self.assertEqual([entity["name"] for entity in data["Entity"]], ["selected"])
        self.assertEqual(
            [attr["name"] for attr in data["EntityAttr"]],
            [selected_attr.name],
        )

    def test_cancelled_export_does_not_create_a_download(self):
        user = self.guest_login()
        job = Job.new_export_configuration_v2(user, "entity")
        job.update(JobStatus.CANCELED)
        job.run(will_delay=False)
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.CANCELED)
        with self.assertRaises(FileNotFoundError):
            job.get_cache()
