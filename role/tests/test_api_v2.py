import yaml

from airone.lib.test import AironeViewTest
from group.models import Group
from role.models import Role
from user.models import User


class ViewTest(AironeViewTest):
    def _create_user(self, name: str):
        return User.objects.create(username=name)

    def _create_group(self, name: str):
        return Group.objects.create(name=name)

    def _create_role(self, name: str):
        return Role.objects.create(name=name)

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

    def test_import_with_permissions(self):
        admin = self.admin_login()

        self._create_user("user1")
        self._create_user("user2")
        self._create_group("group1")
        self._create_group("group2")

        entity = self.create_entity(user=admin, name="test-entity")

        fp = self.open_fixture_file("import_roles_with_permissions.yaml")
        import_data = fp.read().replace("<test_obj_id>", str(entity.id))
        resp = self.client.post("/role/api/v2/import", import_data, content_type="application/yaml")

        self.assertEqual(resp.status_code, 200)
        role = Role.objects.filter(name="role1").first()
        self.assertIsNotNone(role)
        permission = role.permissions.first()
        self.assertEqual(permission, entity.full)

    def test_export(self):
        admin = self.admin_login()

        self._create_user("user1")
        self._create_group("group1")
        role = self._create_role("test-role")

        # set full-permission for created Role instance
        entity = self.create_entity(admin, "Entity")
        role.permissions.add(entity.full)

        resp = self.client.get("/role/api/v2/export")
        data = yaml.load(resp.content.decode("utf-8"))

        self.assertEqual(
            data[0]["permissions"],
            [
                {
                    "obj_id": entity.id,
                    "permission": entity.full.name,
                }
            ],
        )

        # check export data is expected one
        self.assertEqual(
            data,
            [
                {
                    "id": role.id,
                    "name": role.name,
                    "description": "",
                    "users": [],
                    "groups": [],
                    "admin_users": [],
                    "admin_groups": [],
                    "permissions": [
                        {
                            "obj_id": entity.id,
                            "permission": entity.full.name,
                        }
                    ],
                }
            ],
        )
