import json
from datetime import timedelta

from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from unittest.mock import Mock
from user.forms import UsernameBasedPasswordResetForm
from user.models import User
from user.views import PasswordReset


class ViewTest(TestCase):
    def setUp(self):
        self._client = Client()
        self.guest = self._create_user("guest", "guest@example.com")
        self.admin = self._create_user("admin", "admin@example.com", True)

        settings.MIDDLEWARE = [
            x for x in settings.MIDDLEWARE if x != "airone.lib.log.LoggingRequestMiddleware"
        ]

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

    def _admin_login(self):
        self.client.login(username="admin", password="admin")

    def _guest_login(self):
        self.client.login(username="guest", password="guest")

    def _get_active_user_count(self):
        return User.objects.filter(is_active=True).count()

    def test_index_without_login(self):
        resp = self.client.get(reverse("user:index"))
        self.assertEqual(resp.status_code, 303)

    def test_index_with_guest(self):
        self._guest_login()

        resp = self.client.get(reverse("user:index"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["users"], [self.guest])

    def test_index_with_admin(self):
        self._admin_login()

        resp = self.client.get(reverse("user:index"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context["users"]), [self.guest, self.admin])

        # Check context of response
        self.assertTemplateUsed(template_name="list_user.html")
        self.assertEqual(
            [x.username for x in resp.context["users"]],
            [x.username for x in User.objects.filter(is_active=True)],
        )

    def test_create_get_without_login(self):
        resp = self.client.get(reverse("user:create"))
        self.assertEqual(resp.status_code, 303)

    def test_create_get_with_login(self):
        self._admin_login()

        resp = self.client.get(reverse("user:create"))
        self.assertEqual(resp.status_code, 200)

        self.assertTemplateUsed(template_name="create_user.html")

    def test_create_post_without_login(self):
        count = User.objects.count()

        params = {
            "name": "hoge",
            "email": "hoge@example.com",
            "passwd": "puyo",
        }
        resp = self.client.post(reverse("user:do_create"), json.dumps(params), "application/json")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(User.objects.count(), count)  # user should not be created

    def test_create_user_without_permission(self):
        # request of creating an user requires administrative permission
        self._guest_login()

        params = {
            "name": "hoge",
            "email": "hoge@example.com",
            "passwd": "puyo",
        }
        resp = self.client.post(reverse("user:do_create"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.content.decode("utf-8"),
            "This page needs administrative permission to access",
        )

    def test_create_post_with_login(self):
        count = User.objects.count()
        self._admin_login()

        params = {
            "name": "hoge",
            "email": "hoge@example.com",
            "passwd": "puyo",
        }
        resp = self.client.post(reverse("user:do_create"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(User.objects.count(), count + 1)  # user should be created
        self.assertEqual(User.objects.last().username, "hoge")
        self.assertNotEqual(User.objects.last().password, "puyo")
        self.assertFalse(User.objects.last().is_superuser)

    def test_create_user_without_mandatory_param(self):
        count = User.objects.count()
        self._admin_login()

        params = {
            "email": "hoge@example.com",
            "passwd": "puyo",
        }
        resp = self.client.post(reverse("user:do_create"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(User.objects.count(), count)  # user should not be created

    def test_create_user_with_empty_param(self):
        count = User.objects.count()
        self._admin_login()

        params = {
            "user": "hoge",
            "email": "",
            "passwd": "puyo",
        }
        resp = self.client.post(reverse("user:do_create"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(User.objects.count(), count)  # user should be created

    def test_edit_get_without_login(self):
        resp = self.client.get(reverse("user:edit", args=[0]))
        self.assertEqual(resp.status_code, 303)

    def test_edit_get_with_guest_login(self):
        self._guest_login()

        user = User.objects.get(username="admin")
        resp = self.client.get(reverse("user:edit", args=[user.id]))
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode("utf-8"), "You don't have permission to access")

    def test_edit_get_with_admin_login(self):
        self._admin_login()
        self.client.put("/api/v1/user/access_token")

        for username in ["guest", "admin"]:
            user = User.objects.get(username=username)
            resp = self.client.get(reverse("user:edit", args=[user.id]))
            self.assertEqual(resp.status_code, 200)

            # Check context of response
            self.assertTemplateUsed(template_name="edit_user.html")
            self.assertEqual(resp.context["user_id"], user.id)
            self.assertEqual(resp.context["user_name"], user.username)
            self.assertEqual(resp.context["user_email"], user.email)
            self.assertEqual(resp.context["user_is_superuser"], user.is_superuser)
            self.assertEqual(resp.context["token"], user.token if username == "admin" else None)
            self.assertEqual(resp.context["token_lifetime"], user.token_lifetime)
            self.assertEqual(
                resp.context["token_created"],
                (user.token.created.strftime("%Y/%m/%d %H:%M:%S") if username == "admin" else None),
            )
            self.assertEqual(
                resp.context["token_expire"],
                (
                    (user.token.created + timedelta(seconds=user.token_lifetime)).strftime(
                        "%Y/%m/%d %H:%M:%S"
                    )
                    if username == "admin"
                    else None
                ),
            )
            self.assertEqual(resp.context["is_authenticated_by_local"], True)

    def test_edit_for_inactive_user(self):
        self._admin_login()
        user = User.objects.create(username="test", email="test@example.com", is_active=False)

        resp = self.client.get(reverse("user:edit", args=[user.id]))
        self.assertEqual(resp.status_code, 404)

    def test_edit_post_without_login(self):
        user = User.objects.create(username="test", email="test@example.com")

        params = {
            "name": "hoge",  # update guest => hoge
            "email": "hoge@example.com",
            "is_superuser": True,
        }
        resp = self.client.post(
            reverse("user:do_edit", args=[user.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_edit_post_with_login(self):
        self._admin_login()
        user = User.objects.create(username="test", email="test@example.com")
        count = User.objects.count()

        params = {
            "name": "hoge",  # update guest => hoge
            "email": "hoge@example.com",
            "is_superuser": True,
        }
        resp = self.client.post(
            reverse("user:do_edit", args=[user.id]),
            json.dumps(params),
            "application/json",
        )
        user.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(User.objects.count(), count)  # user should be updated
        self.assertEqual(user.username, params["name"])
        self.assertEqual(user.email, params["email"])
        self.assertTrue(user.is_superuser)

    def test_edit_user_with_duplicated_name(self):
        self._admin_login()
        user = User.objects.get(username="guest")

        params = {
            "name": "admin",  # duplicated
            "email": "guest@example.com",
        }
        resp = self.client.post(
            reverse("user:do_edit", args=[user.id]),
            json.dumps(params),
            "application/json",
        )
        user.refresh_from_db()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(user.username, "guest")  # Not updated

    def test_edit_user_with_duplicated_email(self):
        self._admin_login()
        user = User.objects.get(username="guest")

        # create test user
        self._create_user("hoge", "hoge@example.com")

        params = {
            "name": "guest",
            "email": "hoge@example.com",  # duplicated
        }
        resp = self.client.post(
            reverse("user:do_edit", args=[user.id]),
            json.dumps(params),
            "application/json",
        )
        user.refresh_from_db()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(user.username, params["name"])
        self.assertNotEqual(user.email, params["email"])

    def test_edit_user_into_superuser(self):
        self._admin_login()

        # create test user
        user = self._create_user("hoge", "hoge@example.com")

        params = {
            "name": "hoge",
            "email": "hoge@example.com",
            "is_superuser": True,
        }
        resp = self.client.post(
            reverse("user:do_edit", args=[user.id]),
            json.dumps(params),
            "application/json",
        )
        user.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(user.username, params["name"])
        self.assertEqual(user.email, params["email"])
        self.assertTrue(user.is_superuser)

    def test_edit_superuser_into_user(self):
        self._admin_login()

        # create test user
        user = self._create_user("hoge", "hoge@example.com", True)

        params = {
            "name": "hoge",
            "email": "hoge@example.com",
            # If is_superuser doesn't exist, it becomes False
        }
        resp = self.client.post(
            reverse("user:do_edit", args=[user.id]),
            json.dumps(params),
            "application/json",
        )
        user.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(user.username, params["name"])
        self.assertEqual(user.email, params["email"])
        self.assertFalse(user.is_superuser)

    def test_edit_user_params_without_permission(self):
        self._guest_login()

        user = User.objects.get(username="guest")
        params = {
            "name": "hoge",
            "email": "hoge@example.com",
        }
        resp = self.client.post(
            reverse("user:do_edit", args=[user.id]),
            json.dumps(params),
            "application/json",
        )
        user.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(user.username, params["name"])
        self.assertNotEqual(user.email, params["email"])

    def test_set_invalid_token_lifetime(self):
        self._guest_login()

        user = User.objects.get(username="guest")

        for invalid_value in ["abcd", "-1", str(User.MAXIMUM_TOKEN_LIFETIME + 1), ""]:
            params = {
                "name": "hoge",
                "email": "hoge@example.com",
                "token_lifetime": invalid_value,
            }
            resp = self.client.post(
                reverse("user:do_edit", args=[user.id]),
                json.dumps(params),
                "application/json",
            )
            user.refresh_from_db()
            self.assertEqual(resp.status_code, 400)

    def test_set_valid_token_lifetime(self):
        self._admin_login()

        user = User.objects.get(username="guest")
        params = {
            "name": "hoge",
            "email": "hoge@example.com",
            "token_lifetime": "10",
        }
        resp = self.client.post(
            reverse("user:do_edit", args=[user.id]),
            json.dumps(params),
            "application/json",
        )
        user.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(user.token_lifetime, 10)

    def test_edit_post_for_inactive_user(self):
        self._admin_login()
        user = User.objects.create(username="test", email="test@example.com", is_active=False)

        params = {
            "name": "hoge",
            "email": "hoge@example.com",
        }
        resp = self.client.post(
            reverse("user:do_edit", args=[user.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_edit_passwd_get_without_login(self):
        resp = self.client.get(reverse("user:edit_passwd", args=[0]))
        self.assertEqual(resp.status_code, 303)

    def test_edit_passwd_get_with_guest_login(self):
        self._guest_login()

        user = User.objects.get(username="guest")
        resp = self.client.get(reverse("user:edit_passwd", args=[user.id]))
        self.assertEqual(resp.status_code, 200)

        # Check context of response
        self.assertTemplateUsed(template_name="edit_passwd.html")
        self.assertEqual(resp.context["user_id"], user.id)
        self.assertEqual(resp.context["user_name"], user.username)
        self.assertEqual(resp.context["user_grade"], "self")
        self.assertEqual(resp.context["has_password"], True)

    def test_edit_passwd_get_with_admin_login(self):
        self._admin_login()

        user = User.objects.get(username="guest")
        resp = self.client.get(reverse("user:edit_passwd", args=[user.id]))
        self.assertEqual(resp.status_code, 200)

        # Check context of response
        self.assertTemplateUsed(template_name="edit_passwd.html")
        self.assertEqual(resp.context["user_id"], user.id)
        self.assertEqual(resp.context["user_name"], user.username)
        self.assertEqual(resp.context["user_grade"], "super")

    def test_edit_passwd_get_for_inactive_user(self):
        self._admin_login()
        user = User.objects.create(username="test", email="test@example.com", is_active=False)

        resp = self.client.get(reverse("user:edit_passwd", args=[user.id]))
        self.assertEqual(resp.status_code, 404)

    def test_edit_passwd_post_without_login(self):
        params = {
            "id": self.guest.id,
            "old_passwd": "guest",
            "new_passwd": "hoge",
            "chk_passwd": "hoge",
        }
        resp = self.client.post(
            reverse("user:do_edit_passwd", args=[params["id"]]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_edit_passwd_post_with_guest_login(self):
        self._guest_login()
        count = User.objects.count()

        params = {
            "id": self.guest.id,
            "old_passwd": "guest",
            "new_passwd": "hoge",
            "chk_passwd": "hoge",
        }
        resp = self.client.post(
            reverse("user:do_edit_passwd", args=[params["id"]]),
            json.dumps(params),
            "application/json",
        )
        user = User.objects.get(id=params["id"])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(User.objects.count(), count)  # user should be updated
        self.assertTrue(user.check_password(params["new_passwd"]))

    def test_edit_passwd_post_with_admin_login(self):
        self._admin_login()
        count = User.objects.count()

        params = {
            "id": self.guest.id,
            "new_passwd": "hoge",
            "chk_passwd": "hoge",
        }
        resp = self.client.post(
            reverse("user:do_su_edit_passwd", args=[params["id"]]),
            json.dumps(params),
            "application/json",
        )
        user = User.objects.get(id=params["id"])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(User.objects.count(), count)  # user should be updated
        self.assertTrue(user.check_password(params["new_passwd"]))

    def test_edit_passwd_with_guest_login_and_empty_pass(self):
        self._guest_login()

        params = {
            "id": self.guest.id,
            "old_passwd": "guest",
            "new_passwd": "",
            "chk_passwd": "hoge",
        }
        resp = self.client.post(
            reverse("user:do_edit_passwd", args=[params["id"]]),
            json.dumps(params),
            "application/json",
        )
        user = User.objects.get(id=params["id"])
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(user.check_password("guest"))  # Not updated

    def test_edit_passwd_for_inactive_user(self):
        self._admin_login()
        user = User.objects.create(username="test", email="test@example.com", is_active=False)

        params = {
            "id": user.id,
            "old_passwd": "guest",
            "new_passwd": "hoge",
            "chk_passwd": "hoge",
        }
        resp = self.client.post(
            reverse("user:do_edit_passwd", args=[params["id"]]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_edit_passwd_with_admin_login_and_empty_pass(self):
        self._admin_login()

        params = {
            "id": self.guest.id,
            "new_passwd": "",
            "chk_passwd": "hoge",
        }
        resp = self.client.post(
            reverse("user:do_su_edit_passwd", args=[params["id"]]),
            json.dumps(params),
            "application/json",
        )
        user = User.objects.get(id=params["id"])
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(user.check_password("guest"))  # Not updated

    def test_edit_passwd_with_wrong_old_pass(self):
        self._guest_login()

        params = {
            "id": self.guest.id,
            "old_passwd": "hoge",
            "new_passwd": "hoge",
            "chk_passwd": "hoge",
        }
        resp = self.client.post(
            reverse("user:do_edit_passwd", args=[params["id"]]),
            json.dumps(params),
            "application/json",
        )
        user = User.objects.get(id=params["id"])
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(user.check_password("guest"))  # Not updated

    def test_edit_passwd_with_guest_login_and_old_new_pass_duplicated(self):
        self._guest_login()

        params = {
            "id": self.guest.id,
            "old_passwd": "guest",
            "new_passwd": "guest",
            "chk_passwd": "guest",
        }
        resp = self.client.post(
            reverse("user:do_edit_passwd", args=[params["id"]]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_edit_passwd_with_guest_login_and_new_chk_pass_not_equal(self):
        self._guest_login()

        params = {
            "id": self.guest.id,
            "old_passwd": "guest",
            "new_passwd": "hoge",
            "chk_passwd": "fuga",
        }
        resp = self.client.post(
            reverse("user:do_edit_passwd", args=[params["id"]]),
            json.dumps(params),
            "application/json",
        )
        user = User.objects.get(id=params["id"])
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(user.check_password("guest"))  # Not updated

    def test_edit_passwd_with_admin_login_and_new_chk_pass_not_equal(self):
        self._admin_login()

        params = {
            "id": self.guest.id,
            "new_passwd": "hoge",
            "chk_passwd": "fuga",
        }
        resp = self.client.post(
            reverse("user:do_su_edit_passwd", args=[params["id"]]),
            json.dumps(params),
            "application/json",
        )
        user = User.objects.get(id=params["id"])
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(user.check_password("guest"))  # Not updated

    def test_su_edit_passwd_for_inactive_user(self):
        self._admin_login()
        user = User.objects.create(username="test", email="test@example.com", is_active=False)

        params = {
            "id": user.id,
            "old_passwd": "guest",
            "new_passwd": "hoge",
            "chk_passwd": "hoge",
        }
        resp = self.client.post(
            reverse("user:do_su_edit_passwd", args=[params["id"]]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_delete_post(self):
        name = "someuser"

        self._admin_login()

        user = self._create_user(name)
        user_count = User.objects.count()
        active_user_count = self._get_active_user_count()

        resp = self.client.post(
            reverse("user:do_delete", args=[user.id]),
            json.dumps({}),
            "application/json",
        )

        self.assertEqual(resp.status_code, 200)
        # user should not deleted from DB
        self.assertEqual(User.objects.count(), user_count)
        # active user should be decreased
        self.assertEqual(self._get_active_user_count(), active_user_count - 1)

        # user should be inactive
        user = User.objects.get(username__icontains="%s_deleted_" % name)
        self.assertFalse(user.is_active)

    def test_create_user_by_guest_user(self):
        self._guest_login()

        params = {
            "name": "hoge",
            "email": "hoge@example.com",
            "passwd": "puyo",
        }
        resp = self.client.post(reverse("user:do_create"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 400)

    def test_create_admin_user(self):
        self._admin_login()

        params = {
            "name": "hoge",
            "email": "hoge@example.com",
            "passwd": "puyo",
            "is_superuser": "on",
        }
        resp = self.client.post(reverse("user:do_create"), json.dumps(params), "application/json")

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(User.objects.last().is_superuser)

    def test_delete_post_by_guest_user(self):
        self._guest_login()

        user = self._create_user("testuser")

        resp = self.client.post(
            reverse("user:do_delete", args=[user.id]),
            json.dumps({}),
            "application/json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertTrue(User.objects.get(username="testuser").is_active)

    def test_delete_post_for_inactive_user(self):
        self._admin_login()
        user = User.objects.create(username="test", email="test@example.com", is_active=False)

        params = {
            "name": "hoge",
            "email": "hoge@example.com",
        }
        resp = self.client.post(
            reverse("user:do_delete", args=[user.id]),
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 404)

    @patch("user.views.LDAPBackend.is_authenticated", Mock(return_value=True))
    def test_post_chnage_auth_with_correct_password(self):
        self._guest_login()

        resp = self.client.post(
            reverse("user:change_ldap_auth"),
            json.dumps({"ldap_password": "CORRECT_PASSWORD"}),
            "application/json",
        )
        self.guest.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.guest.authenticate_type, User.AUTH_TYPE_LDAP)

    @patch("user.views.LDAPBackend.is_authenticated", Mock(return_value=False))
    def test_post_chnage_auth_with_incorrect_password(self):
        self._guest_login()

        resp = self.client.post(
            reverse("user:change_ldap_auth"),
            json.dumps({"ldap_password": "INCORRECT_PASSWORD"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_post_chnage_auth_with_invalid_parameters(self):
        self._guest_login()

        invalid_parameters = [
            {"invalid_parameter": "value"},
            [{"invalid_parameter": "value"}],
            {"ldap_password": {"invalid_value_type": "value"}},
            {"ldap_password": [1, 2, 3, 4]},
            {"ldap_password": 1234},
            {"ldap_password": ""},
        ]
        for _param in invalid_parameters:
            resp = self.client.post(
                reverse("user:change_ldap_auth"), json.dumps(_param), "application/json"
            )
            self.assertEqual(resp.status_code, 400)

    def test_password_reset_with_invalid_username(self):
        user = self._create_user("testuser", authenticate_type=User.AUTH_TYPE_LDAP)

        # testing this view class requires a complicated client.
        # instead of that, we call the override method directly for now.
        # see also django tests/auth_tests/client.py
        view = PasswordReset()

        form_with_unknown_user = UsernameBasedPasswordResetForm({"username": "unknown"})
        form_with_unknown_user.is_valid()
        resp = view.form_valid(form_with_unknown_user)
        self.assertEqual(resp.status_code, 400)

        form_with_ldap_user = UsernameBasedPasswordResetForm({"username": user.username})
        form_with_ldap_user.is_valid()
        resp = view.form_valid(form_with_ldap_user)
        self.assertEqual(resp.status_code, 400)
