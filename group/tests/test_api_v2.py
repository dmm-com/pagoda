from airone.lib.test import AironeViewTest
from group.models import Group
from user.models import User


class GroupAPITest(AironeViewTest):
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
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["id"], group.id)
        self.assertEqual(len(body[0]["members"]), 1)
        self.assertEqual(body[0]["members"][0]["id"], user.id)

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
