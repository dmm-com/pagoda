import yaml

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
        self.assertEqual(len(body['results']), 1)
        self.assertEqual(body['results'][0]["id"], group.id)
        self.assertEqual(len(body['results'][0]["members"]), 1)
        self.assertEqual(body['results'][0]["members"][0]["id"], user.id)

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
