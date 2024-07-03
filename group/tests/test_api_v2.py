import json

import yaml
from rest_framework import status

from airone.lib.test import AironeViewTest
from group.models import Group
from user.models import User


class ViewTest(AironeViewTest):
    def _create_user(self, name):
        return User.objects.create(username=name)

    def _create_group(self, name):
        return Group.objects.create(name=name)

    def test_list(self):
        self.admin_login()

        user = self._create_user("fuga")
        group = self._create_group("hoge")
        user.groups.add(group)

        resp = self.client.get("/group/api/v2/groups")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["id"], group.id)
        self.assertEqual(len(body["results"][0]["members"]), 1)
        self.assertEqual(body["results"][0]["members"][0]["id"], user.id)

    def test_retrieve(self):
        self.admin_login()

        user = self._create_user("fuga")
        group = self._create_group("hoge")
        user.groups.add(group)

        resp = self.client.get("/group/api/v2/groups/%s" % group.id)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["id"], group.id)
        self.assertEqual(len(body["members"]), 1)
        self.assertEqual(body["members"][0]["id"], user.id)

    def test_update_group(self):
        self.admin_login()

        users = [self._create_user(x) for x in ["userA", "userB", "userC"]]
        group = self._create_group("hoge")
        users[0].groups.add(group)

        update_params = {
            "name": "fuga",
            "members": [str(users[1].id), int(users[2].id)],
        }
        resp = self.client.put(
            "/group/api/v2/groups/%s" % group.id, json.dumps(update_params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # These statements checks whether "group" was updated expectedly
        group.refresh_from_db()
        self.assertEqual(group.name, "fuga")
        self.assertEqual([x.id for x in users[0].groups.all()], [])
        self.assertEqual([x.id for x in users[1].groups.all()], [group.id])
        self.assertEqual([x.id for x in users[2].groups.all()], [group.id])

    def test_import(self):
        self.admin_login()

        fp = self.open_fixture_file("import_group.yaml")
        resp = self.client.post(
            "/group/api/v2/groups/import", fp.read(), content_type="application/yaml"
        )

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(Group.objects.filter(name="Group1").count(), 1)
        self.assertEqual(Group.objects.filter(name="Group2").count(), 1)

    def test_export(self):
        self.admin_login()

        self._create_group("group1")
        self._create_group("group2")

        resp = self.client.get("/group/api/v2/groups/export")
        self.assertEqual(resp.status_code, 200)

        obj = yaml.load(resp.content, Loader=yaml.SafeLoader)
        self.assertTrue(isinstance(obj, list))
        self.assertEqual(len(obj), 2)
