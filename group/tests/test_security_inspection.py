import json

from rest_framework import status

from airone.lib.test import AironeViewTest
from group.models import Group


class ViewTest(AironeViewTest):
    def test_path_traversal(self):
        self.admin_login()

        # create a group to be tested
        group = Group.objects.create(name="hoge")

        # This is a parameter that has path traverasl attacking command
        update_params = {
            "name": "fuga",
            "members": ["1", 2, "cat ../../../../../../../etc/os-release"],
        }
        resp = self.client.put(
            "/group/api/v2/groups/%s" % group.id, json.dumps(update_params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            resp.json(),
            {"members": {"2": [{"message": "A valid integer is required.", "code": "AE-121000"}]}},
        )
