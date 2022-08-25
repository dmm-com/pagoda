import json

from airone.lib.test import AironeViewTest
from entity.models import Entity
from user.models import User


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()
        self.user: User = self.guest_login()
        self.entity: Entity = self.create_entity(
            **{
                "user": self.user,
                "name": "test-entity",
                "attrs": [],
                "webhooks": [],
            }
        )

    def test_custom_exception_handler(self):
        self.add_entry(self.user, "entry1", self.entity)
        params = {
            "name": "entry1",
            "attrs": [],
        }

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % self.entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(
            resp.json()["name"][0][""],
            {"airone_error_code": "AE-220000", "detail": "specified name(entry1) already exists"},
        )
