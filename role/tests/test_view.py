import json

from role.models import Role

from .base import RoleTestBase


class ViewTest(RoleTestBase):
    def setUp(self):
        super(ViewTest, self).setUp()

        self._BASE_CREATE_PARAMS = {
            "name": "Creating Role",
            "description": "explanation of this role",
            "users": [{"id": self.users["userA"].id}],
            "groups": [{"id": self.groups["groupA"].id}],
            "admin_users": [{"id": self.users["userB"].id}],
            "admin_groups": [{"id": self.groups["groupB"].id}],
        }

    def test_get_create(self):
        self.guest_login()

        resp = self.client.get("/role/create/")
        self.assertEqual(resp.status_code, 200)

    def test_post_create(self):
        login_user = self.guest_login()

        # It's necessary to set login-user as a group member of admin_group
        login_user.groups.add(self.groups["groupB"])

        resp = self.client.post(
            "/role/do_create/", json.dumps(self._BASE_CREATE_PARAMS), "application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"msg": 'Succeeded in creating new Role "Creating Role"'})

        # check new Role instance was created
        role = Role.objects.get(name="Creating Role", is_active=True)
        self.assertEqual(role.description, "explanation of this role")
        self.assertEqual([x.username for x in role.users.all()], ["userA"])
        self.assertEqual([x.username for x in role.admin_users.all()], ["userB"])
        self.assertEqual([x.name for x in role.groups.all()], ["groupA"])
        self.assertEqual([x.name for x in role.admin_groups.all()], ["groupB"])

    def test_fail_to_create_with_empty_name(self):
        self.guest_login()

        params = dict(
            self._BASE_CREATE_PARAMS,
            **{
                "name": "",
                "users": [{"id": self.users["userA"].id}],
                "groups": [{"id": self.groups["groupA"].id}],
                "admin_users": [{"id": self.users["userB"].id}],
                "admin_groups": [{"id": self.groups["groupB"].id}],
            }
        )
        resp = self.client.post("/role/do_create/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)

    def test_fail_to_edit_with_empty_name(self):
        self.guest_login()

        params = dict(
            self._BASE_CREATE_PARAMS,
            **{
                "name": "",
            }
        )
        resp = self.client.post(
            "/role/do_edit/%d/" % self.role.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_get_edit(self):
        user = self.guest_login()
        role = Role.objects.create(name="Role")

        # set test user as an administrative one
        role.admin_users.add(user)

        resp = self.client.get("/role/edit/%d/" % role.id)
        self.assertEqual(resp.status_code, 200)

    def test_get_edit_without_permission(self):
        self.guest_login()
        role = Role.objects.create(name="Role")

        resp = self.client.get("/role/edit/%d/" % role.id)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.content.decode("utf-8"),
            "You do not have permission to change this role",
        )

    def test_edit_role(self):
        user = self.guest_login()
        role = Role.objects.create(name="Role")

        # set test user as an administrative one
        role.admin_users.add(user)

        # register userA and groupA as initialized users and groups
        role.users.add(self.users["userA"])
        role.groups.add(self.groups["groupA"])
        role.admin_users.add(self.users["userA"])
        role.admin_groups.add(self.groups["groupA"])

        # It's necessary to set login-user as a group member of admin_group
        user.groups.add(self.groups["groupB"])

        # send a request to reigster userB and groupB as members of the "Role"
        params = dict(
            self._BASE_CREATE_PARAMS,
            **{
                "name": "Edited Role",
                "description": "changing role explanation",
                "users": [{"id": self.users["userB"].id}],
                "groups": [{"id": self.groups["groupB"].id}],
                "admin_users": [{"id": self.users["userB"].id}],
                "admin_groups": [{"id": self.groups["groupB"].id}],
            }
        )
        resp = self.client.post(
            "/role/do_edit/%d/" % role.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        # check role attributes are updated expectedly
        role.refresh_from_db()
        self.assertEqual(role.name, "Edited Role")
        self.assertEqual(role.description, "changing role explanation")
        self.assertEqual([x.username for x in role.users.all()], ["userB"])
        self.assertEqual([x.username for x in role.admin_users.all()], ["userB"])
        self.assertEqual([x.name for x in role.groups.all()], ["groupB"])
        self.assertEqual([x.name for x in role.admin_groups.all()], ["groupB"])

    def test_role_without_admin_member(self):
        self.guest_login()

        params = dict(
            self._BASE_CREATE_PARAMS,
            **{
                "name": "Creating Role to be fail",
            }
        )
        resp = self.client.post("/role/do_create/", json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.content.decode("utf-8"),
            "You can't edit this role. Please set administrative members",
        )
