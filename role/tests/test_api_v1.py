import json
from unittest import mock

from django.urls import reverse

from airone.lib.types import AttrTypeValue
from entry.models import Entry
from role import tasks

from .base import RoleTestBase


class ModelTest(RoleTestBase):
    def setUp(self):
        super(ModelTest, self).setUp()

    def test_delete_invalid_role(self):
        self.guest_login()

        resp = self.client.delete("/role/api/v1/99999/")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.content.decode("utf-8"), '"Role not found(id:99999)"')

    def test_delete_role_without_permission(self):
        self.guest_login()

        resp = self.client.delete("/role/api/v1/%d/" % self.role.id)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(
            resp.content.decode("utf-8"),
            '"Permission error to delete the Role(%s)"' % self.role.name,
        )

    def test_delete_role(self):
        login_user = self.guest_login()

        # set login user as an administrative user of test Role to be deleted
        self.role.admin_users.add(login_user)

        resp = self.client.delete("/role/api/v1/%d/" % self.role.id)
        self.assertEqual(resp.status_code, 204)

    @mock.patch(
        "role.tasks.edit_role_referrals.delay", mock.Mock(side_effect=tasks.edit_role_referrals)
    )
    def test_update_role_referral(self):
        user = self.guest_login()
        user.groups.add(self.groups["groupB"])
        self._BASE_UPDATE_PARAMS = {
            "name": "Creating Role",
            "description": "explanation of this role",
            "users": [{"id": user.id}],
            "groups": [{"id": self.groups["groupA"].id}],
            "admin_users": [{"id": self.users["userB"].id}],
            "admin_groups": [{"id": self.groups["groupB"].id}],
        }

        self.role.admin_users.add(user)

        entity = self.create_entity(
            **{
                "user": user,
                "name": "Entity",
                "attrs": [{"name": "role", "type": AttrTypeValue["role"]}],
            }
        )

        entry = self.add_entry(
            user,
            "entry",
            entity,
            values={"role": self.role},
        )

        entry.register_es()
        resp1 = Entry.search_entries(user, [entity.id], [{"name": "role"}])
        self.assertEqual(resp1["ret_values"][0]["attrs"]["role"]["value"]["name"], "test_role")

        params = dict(
            self._BASE_UPDATE_PARAMS,
            **{
                "name": "test_role_update",
            },
        )
        self.client.post(
            reverse("role:do_edit", args=[self.role.id]),
            json.dumps(params),
            "application/json",
        )
        resp2 = Entry.search_entries(user, [entity.id], [{"name": "role"}])
        self.assertEqual(
            resp2["ret_values"][0]["attrs"]["role"]["value"]["name"], "test_role_update"
        )
