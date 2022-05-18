from .base import RoleTestBase


class ModelTest(RoleTestBase):
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
