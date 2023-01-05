import json
from unittest import mock

import yaml
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.authtoken.models import Token

from airone.lib.test import AironeViewTest
from group.models import Group
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

    def _create_group(self, name):
        return Group.objects.create(name=name)

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

    def test_get_user_token_via_apiv2_without_creation(self):
        self.guest_login()

        resp = self.client.get("/user/api/v2/token/")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json(), {"message": "Not found.", "code": "AE-230000"})

    def test_get_user_token_via_apiv2(self):
        user = self.guest_login()
        token = Token.objects.create(user=user)

        resp = self.client.get("/user/api/v2/token/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"key": str(token)})

    def test_refresh_user_token_via_apiv2(self):
        user = self.guest_login()

        resp = self.client.post("/user/api/v2/token/")
        self.assertEqual(resp.status_code, 200)

        # get user token to compare with response data
        token = Token.objects.get(user=user)
        self.assertEqual(resp.json(), {"key": str(token)})

    def test_import(self):
        self.admin_login()

        self._create_group("Group1")
        self._create_group("Group2")

        fp = self.open_fixture_file("import_user.yaml")
        resp = self.client.post("/user/api/v2/import/", fp.read(), content_type="application/yaml")

        self.assertEqual(resp.status_code, 200)

        user1 = User.objects.filter(username="User1").first()

        self.assertEqual(user1.email, "user1@example.com")
        self.assertEqual(user1.groups.count(), 2)

    def test_export(self):
        self.admin_login()

        group1 = self._create_group("Group1")
        group2 = self._create_group("Group2")

        user1 = self._create_user("user1")
        user1.groups.add(group1)
        user1.groups.add(group2)

        user2 = self._create_user("user2")
        user2.groups.add(group1)

        resp = self.client.get("/user/api/v2/export/")
        self.assertEqual(resp.status_code, 200)

        obj = yaml.load(resp.content, Loader=yaml.SafeLoader)
        self.assertTrue(isinstance(obj, list))
        self.assertEqual(len(obj), 3)

    @mock.patch("user.api_v2.views.EmailMultiAlternatives")
    def test_password_reset(self, mock_email):
        user = self._create_user("user")

        params = {
            "username": user.username,
        }
        resp = self.client.post(
            "/user/api/v2/password_reset", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        mock_email.assert_called_once()

    def test_password_reset_with_unknown_user(self):
        params = {
            "username": "unknown",
        }
        resp = self.client.post(
            "/user/api/v2/password_reset", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_password_reset_confirm(self):
        user = self._create_user("user")
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        password = "new-password"
        params = {
            "uidb64": uidb64,
            "token": token,
            "password1": password,
            "password2": password,
        }
        resp = self.client.post(
            "/user/api/v2/password_reset/confirm", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        updated_user = User.objects.filter(id=user.id).first()
        self.assertIsNotNone(updated_user)
        self.assertTrue(updated_user.check_password(password))

    def test_password_reset_confirm_with_invalid_user(self):
        user = self._create_user("user")
        token = default_token_generator.make_token(user)

        password = "new-password"
        params = {
            "uidb64": "invalid",
            "token": token,
            "password1": password,
            "password2": password,
        }
        resp = self.client.post(
            "/user/api/v2/password_reset/confirm", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_password_reset_confirm_with_invalid_token(self):
        user = self._create_user("user")
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        password = "new-password"
        params = {
            "uidb64": uidb64,
            "token": "invalid",
            "password1": password,
            "password2": password,
        }
        resp = self.client.post(
            "/user/api/v2/password_reset/confirm", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_password_reset_confirm_with_invalid_password(self):
        user = self._create_user("user")
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # too common
        password = "password"
        params = {
            "uidb64": uidb64,
            "token": token,
            "password1": password,
            "password2": password,
        }
        resp = self.client.post(
            "/user/api/v2/password_reset/confirm", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

        # too short
        password = "pw"
        params = {
            "uidb64": uidb64,
            "token": token,
            "password1": password,
            "password2": password,
        }
        resp = self.client.post(
            "/user/api/v2/password_reset/confirm", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

        # unmatch 2 password fields
        params = {
            "uidb64": uidb64,
            "token": token,
            "password1": "new-password",
            "password2": "unmatched-password",
        }
        resp = self.client.post(
            "/user/api/v2/password_reset/confirm", json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_patch_user_password(self):
        user = self.guest_login()
        old_passwd = user.username
        new_passwd = "new-passwd"

        params = {
            "old_passwd": old_passwd,
            "new_passwd": new_passwd,
            "chk_passwd": new_passwd,
        }
        resp = self.client.patch(
            "/user/api/v2/%d/edit_passwd" % user.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        updated_user = User.objects.filter(id=user.id).first()
        self.assertIsNotNone(updated_user)
        self.assertTrue(updated_user.check_password(new_passwd))

    def test_patch_user_password_with_invalid_params(self):
        user = self.guest_login()
        old_passwd = user.username
        new_passwd = "new-passwd"

        # old_passwd is wrong
        params = {
            "old_passwd": "invalid-old-passwd",
            "new_passwd": new_passwd,
            "chk_passwd": new_passwd,
        }
        resp = self.client.patch(
            "/user/api/v2/%d/edit_passwd" % user.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

        # new_passwd doesn't match with chk_passwd
        params = {
            "old_passwd": old_passwd,
            "new_passwd": new_passwd,
            "chk_passwd": "unmatched-passwd",
        }
        resp = self.client.patch(
            "/user/api/v2/%d/edit_passwd" % user.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

        # new_passwd matches with old_passwd
        params = {
            "old_passwd": old_passwd,
            "new_passwd": old_passwd,
            "chk_passwd": old_passwd,
        }
        resp = self.client.patch(
            "/user/api/v2/%d/edit_passwd" % user.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

        # target user doesn't match with a request user
        other = self._create_user("other")
        other_old_passwd = other.username
        params = {
            "old_passwd": other_old_passwd,
            "new_passwd": new_passwd,
            "chk_passwd": new_passwd,
        }
        resp = self.client.patch(
            "/user/api/v2/%d/edit_passwd" % other.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_patch_user_password_by_superuser(self):
        self.admin_login()

        user = self._create_user("user")
        new_passwd = "new-passwd"

        params = {
            "new_passwd": new_passwd,
            "chk_passwd": new_passwd,
        }
        resp = self.client.patch(
            "/user/api/v2/%d/su_edit_passwd" % user.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

        updated_user = User.objects.filter(id=user.id).first()
        self.assertIsNotNone(updated_user)
        self.assertTrue(updated_user.check_password(new_passwd))

    def test_patch_user_password_by_superuser_with_invalid_params(self):
        self.admin_login()

        user = self._create_user("user")
        new_passwd = "new-passwd"

        # new_passwd doesn't match with chk_passwd
        params = {
            "new_passwd": new_passwd,
            "chk_passwd": "invalid-chk-passwd",
        }
        resp = self.client.patch(
            "/user/api/v2/%d/su_edit_passwd" % user.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)

        # request user is not an admin
        self.guest_login()
        params = {
            "new_passwd": new_passwd,
            "chk_passwd": "invalid-chk-passwd",
        }
        resp = self.client.patch(
            "/user/api/v2/%d/su_edit_passwd" % user.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 403)
