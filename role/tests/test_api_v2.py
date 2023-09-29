import json

import yaml

from airone.lib.test import AironeViewTest
from group.models import Group
from role.models import Role
from user.models import User


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        # common processing to create Users and Groups that are specified
        # by test import file
        self.user1 = self._create_user("user1")
        self.user2 = self._create_user("user2")
        self.group1 = self._create_group("group1")
        self.group2 = self._create_group("group2")
        self.user1.groups.add(self.group1)
        self.user2.groups.add(self.group2)

    def _create_user(self, name: str):
        return User.objects.create(username=name)

    def _create_group(self, name: str):
        return Group.objects.create(name=name)

    def _create_role(self, name: str):
        return Role.objects.create(name=name)

    def test_create(self):
        admin = self.admin_login()

        params = {
            "name": "test-role",
            "description": "test-description",
            "users": [self.user1.id],
            "groups": [self.group1.id],
            "admin_users": [self.user2.id, admin.id],
            "admin_groups": [self.group2.id],
        }
        resp = self.client.post("/role/api/v2/", json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(
            resp.json(),
            {
                "is_active": True,
                "name": "test-role",
                "description": "test-description",
                "users": [self.user1.id],
                "groups": [self.group1.id],
                "admin_users": [self.user2.id, admin.id],
                "admin_groups": [self.group2.id],
            },
        )

    def test_create_with_invalid_params(self):
        admin = self.admin_login()

        base_params = {
            "name": "test-role",
            "description": "test-description",
            "users": [self.user1.id],
            "groups": [self.group1.id],
            "admin_users": [self.user2.id, admin.id],
            "admin_groups": [self.group2.id],
        }

        # both admin_users and admin_groups are empty
        params = {
            **base_params,
            "admin_users": [],
            "admin_groups": [],
        }
        resp = self.client.post("/role/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

        # duplicated users
        params = {
            **base_params,
            "users": [self.user1.id],
            "admin_users": [self.user1.id],
        }
        resp = self.client.post("/role/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

        # duplicated groups
        params = {
            **base_params,
            "groups": [self.group1.id],
            "admin_groups": [self.group1.id],
        }
        resp = self.client.post("/role/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

        # login user is not belonging to both admin_users and admin_groups in create data,
        # and the user is not superuser
        self.guest_login()
        params = {
            **base_params,
            "admin_users": [self.user2.id],
            "admin_groups": [self.group2.id],
        }
        resp = self.client.post("/role/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

    def test_update(self):
        admin = self.admin_login()

        params = {
            "name": "test-role",
            "description": "test-description",
            "users": [self.user1.id],
            "groups": [self.group1.id],
            "admin_users": [self.user2.id, admin.id],
            "admin_groups": [self.group2.id],
        }
        resp = self.client.post("/role/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 201)
        role = Role.objects.filter(name="test-role").first()

        params = {
            **params,
            "name": "test-role-updated",
        }
        resp = self.client.put(f"/role/api/v2/{role.id}", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            {
                "is_active": True,
                "name": "test-role-updated",
                "description": "test-description",
                "users": [self.user1.id],
                "groups": [self.group1.id],
                "admin_users": [self.user2.id, admin.id],
                "admin_groups": [self.group2.id],
            },
        )

    def test_update_with_invalid_params(self):
        admin = self.admin_login()

        base_params = {
            "name": "test-role",
            "description": "test-description",
            "users": [self.user1.id],
            "groups": [self.group1.id],
            "admin_users": [self.user2.id, admin.id],
            "admin_groups": [self.group2.id],
        }
        resp = self.client.post("/role/api/v2/", json.dumps(base_params), "application/json")
        self.assertEqual(resp.status_code, 201)
        role = Role.objects.filter(name="test-role").first()

        # both admin_users and admin_groups are empty
        params = {
            **base_params,
            "admin_users": [],
            "admin_groups": [],
        }
        resp = self.client.put(f"/role/api/v2/{role.id}", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

        # duplicated users
        params = {
            **base_params,
            "users": [self.user1.id],
            "admin_users": [self.user1.id],
        }
        resp = self.client.put(f"/role/api/v2/{role.id}", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

        # duplicated groups
        params = {
            **base_params,
            "groups": [self.group1.id],
            "admin_groups": [self.group1.id],
        }
        resp = self.client.put(f"/role/api/v2/{role.id}", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

        # login user is not belonging to both admin_users and admin_groups in update data,
        # and the user is not superuser
        guest = self.guest_login()
        params = {
            **base_params,
            "name": "test-role-managed-by-guest",
            "admin_users": [guest.id],
            "admin_groups": [],
        }
        resp = self.client.post("/role/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 201)
        role = Role.objects.filter(name="test-role-managed-by-guest").first()
        params = {
            **base_params,
            "admin_users": [self.user1.id],
            "admin_groups": [],
        }
        resp = self.client.put(f"/role/api/v2/{role.id}", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

    def test_update_without_permission(self):
        admin = self.admin_login()

        base_params = {
            "name": "test-role",
            "description": "test-description",
            "users": [self.user1.id],
            "groups": [self.group1.id],
            "admin_users": [self.user2.id, admin.id],
            "admin_groups": [self.group2.id],
        }
        resp = self.client.post("/role/api/v2/", json.dumps(base_params), "application/json")
        self.assertEqual(resp.status_code, 201)
        role = Role.objects.filter(name="test-role").first()

        # login user is not belonging to both admin_users and admin_groups,
        # and the user is not superuser
        self.guest_login()
        params = {
            **base_params,
            "admin_users": [self.user2.id],
            "admin_groups": [self.group2.id],
        }
        resp = self.client.put(f"/role/api/v2/{role.id}", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 403)

    def test_delete(self):
        admin = self.admin_login()

        params = {
            "name": "test-role",
            "description": "test-description",
            "users": [self.user1.id],
            "groups": [self.group1.id],
            "admin_users": [self.user2.id, admin.id],
            "admin_groups": [self.group2.id],
        }
        resp = self.client.post("/role/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 201)
        role = Role.objects.filter(name="test-role").first()

        resp = self.client.delete(f"/role/api/v2/{role.id}")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Role.objects.filter(name="test-role", is_active=True).exists())

    def test_delete_without_permission(self):
        admin = self.admin_login()

        params = {
            "name": "test-role",
            "description": "test-description",
            "users": [self.user1.id],
            "groups": [self.group1.id],
            "admin_users": [self.user2.id, admin.id],
            "admin_groups": [self.group2.id],
        }
        resp = self.client.post("/role/api/v2/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 201)
        role = Role.objects.filter(name="test-role").first()

        # login user is not belonging to both admin_users and admin_groups,
        # and the user is not superuser
        self.guest_login()
        resp = self.client.delete(f"/role/api/v2/{role.id}")
        self.assertEqual(resp.status_code, 403)

    def test_import(self):
        self.admin_login()

        fp = self.open_fixture_file("import_roles.yaml")
        resp = self.client.post("/role/api/v2/import", fp.read(), content_type="application/yaml")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Role.objects.filter(name="role1").count(), 1)

    def test_import_for_update(self):
        self.admin_login()

        # create innocent Role instance at first,
        # this will be updated by import processing
        role = Role.objects.create(name="role1")

        # do import processing
        fp = self.open_fixture_file("import_roles_for_update.yaml")
        import_data = fp.read().replace("<role_id>", str(role.id))
        resp = self.client.post("/role/api/v2/import", import_data, content_type="application/yaml")
        self.assertEqual(resp.status_code, 200)

        # This confirms role instance is updated as expected values
        role = Role.objects.filter(name="role1").first()
        self.assertIsNotNone(role)

        self.assertEqual([x.username for x in role.users.all()], ["user2"])
        self.assertEqual([x.username for x in role.admin_users.all()], ["user1"])
        self.assertEqual([x.name for x in role.groups.all()], ["group2"])
        self.assertEqual([x.name for x in role.admin_groups.all()], ["group1"])

    def test_import_with_permissions(self):
        admin = self.admin_login()

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

        # set full-permission for exporting Role instance
        role = self._create_role("test-role")
        entity = self.create_entity(admin, "Entity")
        entity.full.roles.add(role)

        resp = self.client.get("/role/api/v2/export")
        data = yaml.safe_load(resp.content.decode("utf-8"))

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
