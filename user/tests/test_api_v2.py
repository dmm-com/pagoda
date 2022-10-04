from airone.lib.test import AironeViewTest
from user.models import User


class ViewTest(AironeViewTest):
    def _create_user(
        self,
        name,
        email="email",
        is_superuser=False,
        authenticate_type=User.AUTH_TYPE_LOCAL,
    ):
        user = User(
            username=name,
            email=email,
            is_superuser=is_superuser,
            authenticate_type=authenticate_type,
        )
        user.set_password(name)
        user.save()

        return user

    def test_get_user(self):
        login_user = self.guest_login()

        resp = self.client.get("/user/api/v2/%s/" % login_user.id)
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertEqual(body["id"], login_user.id)
        self.assertEqual(body["username"], login_user.username)
        self.assertEqual(body["email"], login_user.email)
        self.assertEqual(body["is_superuser"], login_user.is_superuser)
        self.assertEqual(body["date_joined"], login_user.date_joined.isoformat())
        self.assertEqual(body["token"], None)

        other = self._create_user("test1", "test1@example.com")
        resp = self.client.get("/user/api/v2/%s/" % other.id)
        self.assertEqual(resp.status_code, 403)

    def test_list_user(self):
        login_user = self.guest_login()
        admin_user = self._create_user("admin", "admin@example.com", True)

        resp = self.client.get("/user/api/v2/")
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            resp.json(),
            {
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": admin_user.id,
                        "username": "admin",
                        "email": "admin@example.com",
                        "is_superuser": True,
                        "date_joined": admin_user.date_joined.isoformat(),
                    },
                    {
                        "id": login_user.id,
                        "username": "guest",
                        "email": "",
                        "is_superuser": False,
                        "date_joined": login_user.date_joined.isoformat(),
                    },
                ],
            },
        )

    def test_delete_user(self):
        self.admin_login()

        user: User = User.objects.create(username="user")
        resp = self.client.delete("/user/api/v2/%d/" % user.id)
        self.assertEqual(resp.status_code, 204)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

        # already deleted case
        resp = self.client.delete("/user/api/v2/%d/" % user.id)
        self.assertEqual(resp.status_code, 404)

    def test_delete_user_without_permission(self):
        self.guest_login()

        user: User = User.objects.create(username="user")
        resp = self.client.delete("/user/api/v2/%d/" % user.id)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json(),
            {
                "code": "AE-210000",
                "message": "You do not have permission to perform this action.",
            },
        )
