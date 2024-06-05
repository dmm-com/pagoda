import json
from unittest.mock import Mock, patch

from django.urls import reverse

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrType
from custom_view.tasks.task_custom import update_custom_attribute
from entity.models import Entity
from entry.models import Entry
from entry.tasks import create_entry_attrs, notify_create_entry


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        self.admin = self.admin_login()

        self.entity: Entity = self.create_entity(
            **{
                "user": self.admin,
                "name": "CustomEntity",
                "attrs": [{"name": "val", "type": AttrType.STRING}],
            }
        )

    def test_custom_list_entry(self):
        resp = self.client.get(reverse("entry:index", args=[self.entity.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "custom_view/list_custom_entry.html")

    @patch(
        "entry.tasks.create_entry_attrs.delay",
        Mock(side_effect=create_entry_attrs),
    )
    @patch(
        "entry.tasks.notify_create_entry.delay",
        Mock(side_effect=notify_create_entry),
    )
    @patch("entry.tasks.notify_entry_create", Mock(return_value=Mock()))
    @patch(
        "custom_view.tasks.update_custom_attribute.delay",
        Mock(side_effect=update_custom_attribute),
    )
    def test_custom_task(self):
        resp = self.client.post(
            reverse("entry:do_create", args=[self.entity.id]),
            json.dumps(
                {
                    "entry_name": "hoge",
                    "attrs": [],
                }
            ),
            "application/json",
        )
        self.assertEqual(resp.status_code, 200)
        entry = Entry.objects.get(name="hoge", schema=self.entity)
        self.assertEqual(entry.get_attrv("val").value, "initial value")

    def test_custom_api(self):
        resp = self.client.get("/api/v1/advanced/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), "CustomAPI")

        resp = self.client.get("/api/v2/custom/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), "CustomAPI")
