from airone.lib.test import AironeViewTest
from group.models import Group
from role.models import Role
from user.models import User


class ViewTest(AironeViewTest):
    def _create_user(self, name: str):
        return User.objects.create(username=name)

    def _create_group(self, name: str):
        return Group.objects.create(name=name)

    def test_import(self):
        self.admin_login()

        self._create_user("user1")
        self._create_user("user2")
        self._create_group("group1")
        self._create_group("group2")

        fp = self.open_fixture_file("import_roles.yaml")
        resp = self.client.post("/role/api/v2/import", fp.read(), content_type="application/yaml")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Role.objects.filter(name="role1").count(), 1)
