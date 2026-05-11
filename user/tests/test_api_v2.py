import json
from datetime import timedelta
from unittest import mock
from unittest.mock import Mock, patch

import yaml
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.authtoken.models import Token

from airone.lib.acl import ACLType
from airone.lib.test import AironeViewTest, with_airone_settings
from airone.lib.types import (
    AttrType,
)
from entry import tasks as entry_tasks
from entry.models import Entry
from group.models import Group
from role.models import Role
from user.api_v2.views import UserActivityAPI
from user.models import User


class ViewTest(AironeViewTest):
    def _create_user(
        self,
        name,
        email="email@example.com",
        is_superuser=False,
        is_readonly=False,
        parent_user=None,
        authenticate_type=User.AuthenticateType.AUTH_TYPE_LOCAL,
    ):
        user = User(
            username=name,
            email=email,
            is_superuser=is_superuser,
            is_readonly=is_readonly,
            parent_user=parent_user,
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

        # parent user can retrieve their co-user
        co_user = self._create_user("co_user", "co@example.com", parent_user=login_user)
        resp = self.client.get("/user/api/v2/%s/" % co_user.id)
        self.assertEqual(resp.status_code, 200)

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
                        "is_readonly": False,
                        "date_joined": admin_user.date_joined.isoformat(),
                        "parent_user": None,
                    },
                    {
                        "id": login_user.id,
                        "username": "guest",
                        "email": "",
                        "is_superuser": False,
                        "is_readonly": False,
                        "date_joined": login_user.date_joined.isoformat(),
                        "parent_user": None,
                    },
                ],
            },
        )

    def test_create_user_by_admin(self):
        self.admin_login()

        params = {
            "username": "superuser",
            "email": "superuser@example.com",
            "password": "secret-pass",
            "is_superuser": True,
        }
        resp = self.client.post(
            "/user/api/v2/",
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 201)

        created_user = User.objects.filter(username="superuser").first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.email, "superuser@example.com")
        self.assertTrue(created_user.is_superuser)
        self.assertTrue(created_user.check_password("secret-pass"))
        self.assertFalse(created_user.is_readonly)
        self.assertIsNone(created_user.parent_user)

        # check to prevent creating duplicated username user
        resp = self.client.post(
            "/user/api/v2/",
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()[0]["message"], "User with this username already exists")

    def test_create_superuser_by_guest(self):
        self.guest_login()

        params = {
            "username": "superuser",
            "email": "superuser@example.com",
            "password": "secret-pass",
            "is_superuser": True,
        }
        resp = self.client.post(
            "/user/api/v2/",
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()["message"], "You don't have permission to create superuser")

        # check superuser wasn't created, actually.
        self.assertFalse(User.objects.filter(username="superuser").exists())

    def test_create_readonly_by_guest(self):
        guest_user = self.guest_login()

        # for checking wrong duplication error
        # (creating user will be "guest-new-user", so "newuser" won't be duplicated)
        self._create_user("newuser")

        params = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "secret-pass",
            "is_superuser": False,
        }
        resp = self.client.post(
            "/user/api/v2/",
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 201)

        # check readonly user was created.
        created_user = User.objects.filter(username=guest_user.username + "-newuser").first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.email, guest_user.email)
        self.assertFalse(created_user.is_superuser)
        self.assertTrue(created_user.check_password("secret-pass"))
        self.assertTrue(created_user.is_readonly)
        self.assertEqual(created_user.parent_user, guest_user)

        # check to prevent creating duplicated username user
        resp = self.client.post(
            "/user/api/v2/",
            json.dumps(params),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()["username"][0]["message"], "A user with that username already exists."
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

    def test_delete_own_co_user(self):
        user_guest = self.guest_login()

        # create co-user for guest user
        co_user = self._create_user("co_user", email="co_user@example.com", parent_user=user_guest)

        # delete co-user by parent user
        resp = self.client.delete("/user/api/v2/%d/" % co_user.id)
        self.assertEqual(resp.status_code, 204)

        # check co-user was deleted actually.
        co_user.refresh_from_db()
        self.assertFalse(co_user.is_active)

    def test_get_user_token_via_apiv2_without_creation(self):
        self.guest_login()

        resp = self.client.get("/user/api/v2/token/")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json(), {"message": "No Token matches the given query.", "code": "AE-230000"}
        )

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

    def test_patch_co_user_password_by_guest(self):
        user = self.guest_login()

        co_user = self._create_user("co_user", parent_user=user)
        params = {
            "old_passwd": co_user.username,
            "new_passwd": "new-passwd",
            "chk_passwd": "new-passwd",
        }
        resp = self.client.patch(
            "/user/api/v2/%d/edit_passwd" % co_user.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 200)

    def test_patch_other_user_password_by_guest(self):
        self.guest_login()

        other_user = self._create_user("other")
        params = {
            "old_passwd": "other",
            "new_passwd": "new-passwd",
            "chk_passwd": "new-passwd",
        }
        resp = self.client.patch(
            "/user/api/v2/%d/edit_passwd" % other_user.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()["non_field_errors"][0]["message"],
            "You don't have permission to access this object",
        )

    @with_airone_settings(
        {
            "PASSWORD_RESET_DISABLED": True,
        }
    )
    def test_patch_user_password_when_PASSWORD_RESET_DISABLED_is_set(self):
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
        self.assertEqual(resp.status_code, 403)

        # check password wasn't changed
        self.assertEqual(
            resp.json(), {"message": "It is not allowed to change password", "code": "AE-210000"}
        )
        self.assertFalse(user.check_password(new_passwd))
        self.assertTrue(user.check_password(old_passwd))

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

    @patch("user.api_v2.serializers.LDAPBackend.is_authenticated", Mock(return_value=True))
    def test_post_change_auth_with_correct_password(self):
        login_user = self.guest_login()

        resp = self.client.patch(
            "/user/api/v2/%d/auth" % login_user.id,
            json.dumps({"ldap_password": "CORRECT_PASSWORD"}),
            "application/json",
        )
        login_user.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(login_user.authenticate_type, User.AuthenticateType.AUTH_TYPE_LDAP)

    def test_post_change_auth_with_user_already_enables_ldap(self):
        login_user = self.guest_login()
        login_user.authenticate_type = User.AuthenticateType.AUTH_TYPE_LDAP
        login_user.save(update_fields=["authenticate_type"])

        resp = self.client.patch(
            "/user/api/v2/%d/auth" % login_user.id,
            json.dumps({"ldap_password": "CORRECT_PASSWORD"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)

    @patch("user.api_v2.serializers.LDAPBackend.is_authenticated", Mock(return_value=False))
    def test_post_change_auth_with_incorrect_password(self):
        login_user = self.guest_login()

        resp = self.client.patch(
            "/user/api/v2/%d/auth" % login_user.id,
            json.dumps({"ldap_password": "INCORRECT_PASSWORD"}),
            "application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_post_change_auth_with_invalid_parameters(self):
        login_user = self.guest_login()

        invalid_parameters = [
            {"invalid_parameter": "value"},
            [{"invalid_parameter": "value"}],
            {"ldap_password": {"invalid_value_type": "value"}},
            {"ldap_password": [1, 2, 3, 4]},
            {"ldap_password": ""},
        ]
        for _param in invalid_parameters:
            resp = self.client.patch(
                "/user/api/v2/%d/auth" % login_user.id, json.dumps(_param), "application/json"
            )
            self.assertEqual(resp.status_code, 400)

    def test_refresh_co_user_token_by_parent(self):
        parent_user = self.guest_login()
        co_user = self._create_user("co_user", parent_user=parent_user)

        resp = self.client.post("/user/api/v2/%d/token/" % co_user.id)
        self.assertEqual(resp.status_code, 200)

        token = Token.objects.get(user=co_user)
        self.assertEqual(resp.json(), {"key": str(token)})

    def test_refresh_co_user_token_by_non_parent(self):
        self.guest_login()
        other_user = self._create_user("other_user")

        resp = self.client.post("/user/api/v2/%d/token/" % other_user.id)
        self.assertEqual(resp.status_code, 403)


class RecentActivityAPITest(ViewTest):
    def setUp(self):
        super().setUp()

    @mock.patch(
        "entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=entry_tasks.create_entry_v2)
    )
    @mock.patch("entry.tasks.edit_entry_v2.delay", mock.Mock(side_effect=entry_tasks.edit_entry_v2))
    @mock.patch(
        "entry.tasks.delete_entry_v2.delay", mock.Mock(side_effect=entry_tasks.delete_entry_v2)
    )
    def test_get_recent_activity(self):
        user_guest = self.guest_login()

        # prepare test Users, Models, and Items
        DAIMYO_NAMES = ["MatsunagaHisahide", "OdaNobunaga", "ToyotomiHideyoshi"]
        daimyos = {x: self._create_user(x) for x in DAIMYO_NAMES}
        model_prefecture = self.create_entity(
            user_guest,
            "Prefecture",
            attrs=[
                {"name": "ruler", "type": AttrType.STRING},
            ],
        )
        model_castle = self.create_entity(
            user_guest,
            "Castle",
            attrs=[
                {"name": "location", "type": AttrType.OBJECT, "ref": model_prefecture.id},
                {"name": "designer", "type": AttrType.STRING},
            ],
        )
        item_prefectures = {
            x: self.add_entry(user_guest, x, model_prefecture)
            for x in [
                "Osaka",
                "Kyoto",
                "Nara",
                "Shiga",
                "Fukui",
                "Okayama",
            ]
        }
        item_castles = {
            castle_name: self.add_entry(
                user_guest,
                castle_name,
                model_castle,
                values={
                    "location": item_prefectures[location_name].id,
                },
            )
            for (castle_name, location_name) in [
                ("TsutuiCastle", "Nara"),
                ("IchijodaniCastle", "Fukui"),
                ("BichuTakamatsuCastle", "Okayama"),
            ]
        }

        # change ruler of Kyoto prefecture over the course of history
        attr_ruler_of_kyoto = model_prefecture.attrs.get(name="ruler")
        for daimyo_name in DAIMYO_NAMES:
            # create each castles by specified daimyos
            self.client.login(username=daimyo_name, password=daimyo_name)
            params = {
                "name": item_prefectures["Kyoto"].name,
                "attrs": [
                    {"id": attr_ruler_of_kyoto.id, "value": daimyo_name},
                ],
            }
            resp = self.client.put(
                "/entry/api/v2/%s/" % item_prefectures["Kyoto"].id,
                json.dumps(params),
                "application/json",
            )
            self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # record each castle by each daimyos
        attr_location_of_castle = model_castle.attrs.get(name="location")
        attr_designer_of_castle = model_castle.attrs.get(name="designer")
        for daimyo_name, castle_name, location_name, designer_name in [
            ("MatsunagaHisahide", "TamonzanCastle", "Nara", ""),
            ("OdaNobunaga", "AzuchiCastle", "Shiga", "NiwaNagahide"),
            ("ToyotomiHideyoshi", "OsakaCastle", "Osaka", "KurodaKanbei"),
        ]:
            # create each castles by specified daimyos
            self.client.login(username=daimyo_name, password=daimyo_name)

            # send API request to create castle item
            params = {
                "name": castle_name,
                "attrs": [
                    {"id": attr_location_of_castle.id, "value": item_prefectures[location_name].id},
                    {"id": attr_designer_of_castle.id, "value": designer_name},
                ],
            }
            resp = self.client.post(
                "/entity/api/v2/%s/entries/" % model_castle.id,
                json.dumps(params),
                "application/json",
            )
            self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # destroy castles by each daimyos
        for daimyo_name, castle_name, location_name in [
            ("MatsunagaHisahide", "TsutuiCastle", "Nara"),
            ("OdaNobunaga", "IchijodaniCastle", "Fukui"),
            ("ToyotomiHideyoshi", "BichuTakamatsuCastle", "Okayama"),
        ]:
            # create each castles by specified daimyos
            self.client.login(username=daimyo_name, password=daimyo_name)

            # send API request to delete castle item
            item_castle = Entry.objects.filter(name=castle_name, schema=model_castle).first()
            resp = self.client.delete(
                "/entry/api/v2/%s/" % item_castle.id, None, "application/json"
            )
            self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Here is the main processing of this test case
        TGT_USERNAME = "OdaNobunaga"
        self.client.login(username=TGT_USERNAME, password=TGT_USERNAME)

        # call API to get recent activity of target user
        resp = self.client.get("/user/api/v2/%s/activity" % daimyos[TGT_USERNAME].id)
        self.assertEqual(resp.status_code, 200)

        # response data expect following data structure for each activity
        """
        {
            "action_type": "create" | "update" | "delete",
            "target_type": "item" | "model",
            "target": {
                "id": 100,
                "name": "entry name",
                "attr": {
                    "id": 200,
                    "name": "attr name",
                    "type": AttrType.STRING | AttrType.OBJECT | ...,
                    "curr_value": {
                        "id": 300,
                        "value": "current value",
                        "user": {
                            "id": 500,
                            "username": "updated user name",
                        },
                    },
                    "prev_value": {
                        "id": 400,
                        "value": "previous value",
                        "user": {
                            "id": 600,
                            "username": "previous updated user name",
                        },
                    },
                }
                "model": {
                    "id": 10,
                    "name": "model name",
                },
            },
            "timestamp": "2024-01-01T00:00:00Z",
        }
        """
        item_azuchi = Entry.objects.get(name="AzuchiCastle", schema=model_castle)

        # last activity is deleting castle by OdaNobunaga, so check it first
        self.assertEqual(resp.json()[0]["action_type"], "delete")
        self.assertEqual(resp.json()[0]["target_type"], "item")
        self.assertEqual(resp.json()[0]["target"]["id"], item_castles["IchijodaniCastle"].id)
        self.assertEqual(resp.json()[0]["target"]["model"]["id"], model_castle.id)

        # before that target user update attribute of created Item (designer is newer than location)
        self.assertEqual(resp.json()[1]["action_type"], "update")
        self.assertEqual(resp.json()[1]["target_type"], "item")
        self.assertEqual(resp.json()[1]["target"]["id"], item_azuchi.id)
        self.assertEqual(resp.json()[1]["target"]["attr"]["name"], "designer")
        self.assertEqual(resp.json()[1]["target"]["attr"]["type"], AttrType.STRING)
        self.assertEqual(resp.json()[1]["target"]["attr"]["curr_value"]["value"], "NiwaNagahide")
        self.assertEqual(resp.json()[1]["target"]["model"]["id"], model_castle.id)

        # before that target user update another attribute of created Item
        self.assertEqual(resp.json()[2]["action_type"], "update")
        self.assertEqual(resp.json()[2]["target_type"], "item")
        self.assertEqual(resp.json()[2]["target"]["id"], item_azuchi.id)
        self.assertEqual(resp.json()[2]["target"]["attr"]["name"], "location")
        self.assertEqual(resp.json()[2]["target"]["attr"]["type"], AttrType.OBJECT)
        self.assertEqual(
            resp.json()[2]["target"]["attr"]["curr_value"]["value"]["id"],
            item_prefectures["Shiga"].id,
        )
        self.assertEqual(resp.json()[2]["target"]["attr"]["curr_value"]["value"]["name"], "Shiga")
        self.assertEqual(
            resp.json()[2]["target"]["attr"]["curr_value"]["value"]["model"]["id"],
            model_prefecture.id,
        )
        self.assertEqual(resp.json()[2]["target"]["model"]["id"], model_castle.id)

        # before that target user create castle item
        self.assertEqual(resp.json()[3]["action_type"], "create")
        self.assertEqual(resp.json()[3]["target_type"], "item")
        self.assertEqual(resp.json()[3]["target"]["id"], item_azuchi.id)
        self.assertEqual(resp.json()[3]["target"]["model"]["id"], model_castle.id)

        # before that target user update attribute of prefecture item
        self.assertEqual(resp.json()[4]["action_type"], "update")
        self.assertEqual(resp.json()[4]["target_type"], "item")
        self.assertEqual(resp.json()[4]["target"]["id"], item_prefectures["Kyoto"].id)
        self.assertEqual(resp.json()[4]["target"]["attr"]["name"], "ruler")
        self.assertEqual(resp.json()[4]["target"]["attr"]["curr_value"]["value"], "OdaNobunaga")
        self.assertEqual(
            resp.json()[4]["target"]["attr"]["prev_value"]["value"], "MatsunagaHisahide"
        )
        self.assertEqual(
            resp.json()[4]["target"]["attr"]["prev_value"]["user"]["id"],
            daimyos["MatsunagaHisahide"].id,
        )
        self.assertEqual(resp.json()[4]["target"]["model"]["id"], model_prefecture.id)

    def test_prevent_getting_whole_records(self):
        """
        This test case is for checking the prevention of getting whole records of
        recent activity. When a user has many activities, it is not appropriate
        to return all records of them at once.
        """
        user = self.guest_login()
        limit = UserActivityAPI.LIMIT_RECORDS

        entity = self.create_entity(
            user, "TestModel", attrs=[{"name": "val", "type": AttrType.STRING}]
        )

        # Create limit+1 entries to exceed the create activity limit
        entries = [self.add_entry(user, "item-%d" % i, entity) for i in range(limit + 1)]

        # Delete limit+1 entries to exceed the delete activity limit
        for entry in entries:
            entry.delete(deleted_user=user)

        # Create limit+1 attribute updates to exceed the update activity limit
        live = self.add_entry(user, "live", entity)
        attr = live.attrs.get(schema__name="val")
        for i in range(limit + 1):
            attr.add_value(user, "v%d" % i)

        resp = self.client.get("/user/api/v2/%s/activity" % user.id)
        self.assertEqual(resp.status_code, 200)

        activities = resp.json()
        self.assertLessEqual(sum(1 for a in activities if a["action_type"] == "create"), limit)
        self.assertLessEqual(sum(1 for a in activities if a["action_type"] == "update"), limit)
        self.assertLessEqual(sum(1 for a in activities if a["action_type"] == "delete"), limit)

    def test_get_activity_within_minutes(self):
        """
        When within_minutes is specified, all activities within that window are returned
        regardless of LIMIT_RECORDS.
        """
        user = self.guest_login()
        limit = UserActivityAPI.LIMIT_RECORDS

        entity = self.create_entity(
            user, "TestModel", attrs=[{"name": "val", "type": AttrType.STRING}]
        )

        # Create limit+1 entries so the count exceeds LIMIT_RECORDS
        entries = [self.add_entry(user, "item-%d" % i, entity) for i in range(limit + 1)]

        # Backdate one entry to be outside the within_minutes window
        old_entry = entries[0]
        Entry.objects.filter(pk=old_entry.id).update(
            created_time=timezone.now() - timedelta(minutes=60)
        )

        resp = self.client.get("/user/api/v2/%s/activity?within_minutes=30" % user.id)
        self.assertEqual(resp.status_code, 200)

        create_activities = [a for a in resp.json() if a["action_type"] == "create"]
        # Should return limit entries (limit+1 created, 1 backdated outside window)
        self.assertEqual(len(create_activities), limit)

    def test_get_activity_with_since_timestamp(self):
        user = self.guest_login()

        # create items sparsely over time
        model = self.create_entity(
            user, "TestModel", attrs=[{"name": "val", "type": AttrType.STRING}]
        )
        item = self.add_entry(user, "item", model)
        attr = item.attrs.get(schema__name="val")

        for i in range(3):
            changed_attrv = attr.add_value(user, "changed-%d" % i)

            # backdate its created_time for each 20 minutes
            changed_attrv.created_time = timezone.now() - timedelta(minutes=(20 * i))
            changed_attrv.save(update_fields=["created_time"])

        # Remove the initial empty AttributeValue auto-created during entry registration
        # (register_es calls get_latest_value which creates one; prev_value FK is SET_NULL)
        attr.values.filter(value="").delete()

        # Without since: all 3 update records are returned
        resp = self.client.get("/user/api/v2/%s/activity" % user.id)
        self.assertEqual(resp.status_code, 200)
        update_records = [a for a in resp.json() if a["action_type"] == "update"]
        self.assertEqual(len(update_records), 3)

        # since=10 min ago: only i=0 (0 min ago) passes the gte filter, giving 1 record
        since_iso = (timezone.now() - timedelta(minutes=10)).isoformat()
        resp = self.client.get("/user/api/v2/%s/activity?since=%s" % (user.id, since_iso))
        self.assertEqual(resp.status_code, 200)
        update_records = [a for a in resp.json() if a["action_type"] == "update"]
        self.assertEqual(len(update_records), 1)

    def test_get_activity_since_invalid(self):
        user = self.guest_login()

        resp = self.client.get("/user/api/v2/%s/activity?since=not-a-datetime" % user.id)
        self.assertEqual(resp.status_code, 400)

    def test_get_activity_within_minutes_invalid(self):
        user = self.guest_login()

        resp = self.client.get("/user/api/v2/%s/activity?within_minutes=abc" % user.id)
        self.assertEqual(resp.status_code, 400)

        resp = self.client.get("/user/api/v2/%s/activity?within_minutes=0" % user.id)
        self.assertEqual(resp.status_code, 400)

        resp = self.client.get("/user/api/v2/%s/activity?within_minutes=-5" % user.id)
        self.assertEqual(resp.status_code, 400)

    def test_get_activity_filters_by_permission(self):
        """
        Activities for models/items/attributes the requesting user lacks permission to
        should be excluded from the response.
        """
        admin = self._create_user("admin", is_superuser=True)
        activity_user = self._create_user("activity_user")
        self._create_user("viewing_user")

        public_entity = self.create_entity(
            admin, "PublicModel", attrs=[{"name": "val", "type": AttrType.STRING}]
        )
        private_entity = self.create_entity(
            admin, "PrivateModel", attrs=[{"name": "val", "type": AttrType.STRING}]
        )

        # create entries while both entities are still public so complement_attrs succeeds
        public_entry = self.add_entry(
            activity_user, "pub-item", public_entity, values={"val": "v0"}
        )
        private_entry = self.add_entry(
            activity_user, "priv-item", private_entity, values={"val": "v0"}
        )

        # update attribute values
        public_entry.attrs.get(schema__name="val").add_value(activity_user, "v1")
        private_entry.attrs.get(schema__name="val").add_value(activity_user, "v1")

        # delete entries
        public_entry.delete(deleted_user=activity_user)
        private_entry.delete(deleted_user=activity_user)

        # now restrict private_entity so viewing_user has no permission
        private_entity.is_public = False
        private_entity.default_permission = ACLType.Nothing.id
        private_entity.save()

        # viewing_user requests activity of activity_user
        self.client.login(username="viewing_user", password="viewing_user")
        resp = self.client.get("/user/api/v2/%s/activity" % activity_user.id)
        self.assertEqual(resp.status_code, 200)

        activities = resp.json()
        target_models = {a["target"]["model"]["id"] for a in activities}
        self.assertIn(public_entity.id, target_models)
        self.assertNotIn(private_entity.id, target_models)

        # --- additional case: Attribute-instance permission filters update activity ---
        # Entity and entry remain public; only the Attribute instance itself is restricted.
        target_model = self.create_entity(
            admin,
            "ModelForAttrPermTest",
            attrs=[
                {"name": "secret1", "type": AttrType.STRING},
                {"name": "secret2", "type": AttrType.STRING},
            ],
        )
        target_item = self.add_entry(
            activity_user, "item-for-attr-perm", target_model, values={"secret1": "init", "secret2": "init"}
        )

        # update activity for secret_attr should be visible to viewing_user
        # at this point since the Attribute instance is still public.
        for attr in target_item.attrs.all():
            attr.add_value(activity_user, "change " + attr.schema.name)

        # with the attribute still public, viewing_user sees the update activities
        # (add_entry itself also records an AttributeValue, so there are at least two)
        resp = self.client.get("/user/api/v2/%s/activity" % activity_user.id)
        self.assertEqual(resp.status_code, 200)

        update_activities = [
            a
            for a in resp.json()
            if a["action_type"] == "update" and a["target"]["model"]["id"] == target_model.id
        ]
        self.assertGreater(len(update_activities), 0)

        # set permissoins to prevent viewing_user from seeing the AttributeValue
        # that was updated in the previous step
        model_attr_secret1 = target_model.attrs.get(name="secret1")
        item_attr_secret2 = target_item.attrs.get(schema__name="secret2")
        for attr in [model_attr_secret1, item_attr_secret2]:
            attr.is_public = False
            attr.default_permission = ACLType.Nothing.id
            attr.save()

        resp = self.client.get("/user/api/v2/%s/activity" % activity_user.id)
        self.assertEqual(resp.status_code, 200)

        update_activities = [
            a
            for a in resp.json()
            if a["action_type"] == "update" and a["target"]["model"]["id"] == target_model.id
        ]
        self.assertEqual(len(update_activities), 0)

    def _setup_attr_update_activity(
        self, user: User, attr_name: str, attr_type: AttrType, values: list
    ):
        """Create model/item and update attr via API. values=[initial, updated].
        Returns (model, item). The most recent PUT sets values[-1]; prev is values[-2]."""
        model = self.create_entity(
            user, "TestModel", attrs=[{"name": attr_name, "type": attr_type}]
        )
        item = self.add_entry(user, "TestItem", model, values={attr_name: values[0]})
        item.attrs.get(schema__name=attr_name).add_value(user, values[1])

        target_attr = model.attrs.get(name=attr_name)
        for value in values:
            params = {
                "name": item.name,
                "attrs": [{"id": target_attr.id, "value": value}],
            }
            resp = self.client.put(
                "/entry/api/v2/%s/" % item.id,
                json.dumps(params),
                "application/json",
            )
            self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        return model, item

    def _assert_latest_update_activity(
        self,
        resp,
        item,
        model,
        attr_name: str,
        attr_type: AttrType,
        curr_value,
        prev_value,
    ):
        """Assert that resp.json()[0] is a correctly structured update activity."""
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["action_type"], "update")
        self.assertEqual(resp.json()[0]["target_type"], "item")
        self.assertEqual(resp.json()[0]["target"]["id"], item.id)
        self.assertEqual(resp.json()[0]["target"]["attr"]["name"], attr_name)
        self.assertEqual(resp.json()[0]["target"]["attr"]["type"], attr_type)
        self.assertEqual(resp.json()[0]["target"]["attr"]["curr_value"]["value"], curr_value)
        self.assertEqual(resp.json()[0]["target"]["attr"]["prev_value"]["value"], prev_value)
        self.assertEqual(resp.json()[0]["target"]["model"]["id"], model.id)

    def test_get_activity_has_text_typed_record(self):
        user = self.guest_login()

        # prepare to create Model and Item for testing user activity API
        model, item = self._setup_attr_update_activity(
            user, "text_attr", AttrType.TEXT, ["test", "updated text"]
        )

        # call API to get recent activity of target user
        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        # check that the latest activity has expected data
        self._assert_latest_update_activity(
            resp, item, model, "text_attr", AttrType.TEXT, "updated text", "test"
        )

    def test_get_activity_has_boolean_typed_record(self):
        user = self.guest_login()

        # prepare to create Model and Item for testing user activity API
        model, item = self._setup_attr_update_activity(
            user, "bool_attr", AttrType.BOOLEAN, [False, True]
        )

        # call API to get recent activity of target user
        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        # check that the latest activity has expected data
        self._assert_latest_update_activity(
            resp, item, model, "bool_attr", AttrType.BOOLEAN, True, False
        )

    def test_get_activity_has_array_string_typed_record(self):
        user = self.guest_login()

        # prepare to create Model and Item for testing user activity API
        model, item = self._setup_attr_update_activity(
            user,
            "arr_str_attr",
            AttrType.ARRAY_STRING,
            [["foo", "bar"], ["baz", "qux"]],
        )

        # call API to get recent activity of target user
        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        # check that the latest activity has expected data
        self._assert_latest_update_activity(
            resp,
            item,
            model,
            "arr_str_attr",
            AttrType.ARRAY_STRING,
            ["baz", "qux"],
            ["foo", "bar"],
        )

    def test_get_activity_has_named_object_typed_record(self):
        user = self.guest_login()

        # prepare referral model and item
        ref_model = self.create_entity(user, "RefModel")
        ref_item = self.add_entry(user, "RefItem", ref_model)

        # prepare to create Model and Item for testing user activity API
        model, item = self._setup_attr_update_activity(
            user,
            "named_obj_attr",
            AttrType.NAMED_OBJECT,
            [
                {"name": "label1", "id": ref_item.id},
                {"name": "label2", "id": ref_item.id},
            ],
        )

        # call API to get recent activity of target user
        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        # check that the latest activity has expected data
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["action_type"], "update")
        self.assertEqual(resp.json()[0]["target"]["attr"]["name"], "named_obj_attr")
        self.assertEqual(resp.json()[0]["target"]["attr"]["type"], AttrType.NAMED_OBJECT)
        self.assertEqual(resp.json()[0]["target"]["model"]["id"], model.id)

        curr = resp.json()[0]["target"]["attr"]["curr_value"]["value"]
        self.assertEqual(curr["name"], "label2")
        self.assertEqual(curr["object"]["id"], ref_item.id)
        self.assertEqual(curr["object"]["name"], ref_item.name)
        self.assertEqual(curr["object"]["model"]["id"], ref_model.id)

        prev = resp.json()[0]["target"]["attr"]["prev_value"]["value"]
        self.assertEqual(prev["name"], "label1")
        self.assertEqual(prev["object"]["id"], ref_item.id)
        self.assertEqual(prev["object"]["name"], ref_item.name)
        self.assertEqual(prev["object"]["model"]["id"], ref_model.id)

    def test_get_activity_has_number_typed_record(self):
        user = self.guest_login()
        model, item = self._setup_attr_update_activity(
            user, "num_attr", AttrType.NUMBER, [1.5, 2.5]
        )

        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        self._assert_latest_update_activity(
            resp, item, model, "num_attr", AttrType.NUMBER, 2.5, 1.5
        )

    def test_get_activity_has_date_typed_record(self):
        user = self.guest_login()
        model, item = self._setup_attr_update_activity(
            user, "date_attr", AttrType.DATE, ["2024-01-01", "2024-06-15"]
        )

        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        self._assert_latest_update_activity(
            resp, item, model, "date_attr", AttrType.DATE, "2024-06-15", "2024-01-01"
        )

    def test_get_activity_has_datetime_typed_record(self):
        user = self.guest_login()
        model, item = self._setup_attr_update_activity(
            user,
            "dt_attr",
            AttrType.DATETIME,
            ["2024-01-01T00:00:00+00:00", "2024-06-15T12:30:00+00:00"],
        )

        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["target"]["attr"]["type"], AttrType.DATETIME)
        curr = resp.json()[0]["target"]["attr"]["curr_value"]["value"]
        prev = resp.json()[0]["target"]["attr"]["prev_value"]["value"]
        self.assertTrue(curr.startswith("2024-06-15"))
        self.assertTrue(prev.startswith("2024-01-01"))

    def test_get_activity_has_group_typed_record(self):
        user = self.guest_login()
        group1 = Group.objects.create(name="Group1")
        group2 = Group.objects.create(name="Group2")
        model, item = self._setup_attr_update_activity(
            user, "group_attr", AttrType.GROUP, [group1.id, group2.id]
        )

        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["target"]["attr"]["type"], AttrType.GROUP)
        curr = resp.json()[0]["target"]["attr"]["curr_value"]["value"]
        prev = resp.json()[0]["target"]["attr"]["prev_value"]["value"]
        self.assertEqual(curr["id"], group2.id)
        self.assertEqual(curr["name"], group2.name)
        self.assertEqual(prev["id"], group1.id)
        self.assertEqual(prev["name"], group1.name)

    def test_get_activity_has_role_typed_record(self):
        user = self.guest_login()
        role1 = Role.objects.create(name="Role1")
        role2 = Role.objects.create(name="Role2")
        model, item = self._setup_attr_update_activity(
            user, "role_attr", AttrType.ROLE, [role1.id, role2.id]
        )

        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["target"]["attr"]["type"], AttrType.ROLE)
        curr = resp.json()[0]["target"]["attr"]["curr_value"]["value"]
        prev = resp.json()[0]["target"]["attr"]["prev_value"]["value"]
        self.assertEqual(curr["id"], role2.id)
        self.assertEqual(curr["name"], role2.name)
        self.assertEqual(prev["id"], role1.id)
        self.assertEqual(prev["name"], role1.name)

    def test_get_activity_has_array_number_typed_record(self):
        user = self.guest_login()
        model, item = self._setup_attr_update_activity(
            user, "arr_num_attr", AttrType.ARRAY_NUMBER, [[1.5, 2.5], [3.5, 4.5]]
        )

        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        self._assert_latest_update_activity(
            resp, item, model, "arr_num_attr", AttrType.ARRAY_NUMBER, [3.5, 4.5], [1.5, 2.5]
        )

    def test_get_activity_has_array_object_typed_record(self):
        user = self.guest_login()
        ref_model = self.create_entity(user, "RefModel")
        ref_item1 = self.add_entry(user, "RefItem1", ref_model)
        ref_item2 = self.add_entry(user, "RefItem2", ref_model)
        model, item = self._setup_attr_update_activity(
            user,
            "arr_obj_attr",
            AttrType.ARRAY_OBJECT,
            [[ref_item1.id], [ref_item2.id]],
        )

        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["target"]["attr"]["type"], AttrType.ARRAY_OBJECT)
        curr = resp.json()[0]["target"]["attr"]["curr_value"]["value"]
        prev = resp.json()[0]["target"]["attr"]["prev_value"]["value"]
        self.assertEqual(len(curr), 1)
        self.assertEqual(curr[0]["id"], ref_item2.id)
        self.assertEqual(curr[0]["name"], ref_item2.name)
        self.assertEqual(curr[0]["model"]["id"], ref_model.id)
        self.assertEqual(len(prev), 1)
        self.assertEqual(prev[0]["id"], ref_item1.id)

    def test_get_activity_has_array_named_object_typed_record(self):
        user = self.guest_login()
        ref_model = self.create_entity(user, "RefModel")
        ref_item = self.add_entry(user, "RefItem", ref_model)
        model, item = self._setup_attr_update_activity(
            user,
            "arr_named_attr",
            AttrType.ARRAY_NAMED_OBJECT,
            [
                [{"name": "label1", "id": ref_item.id}],
                [{"name": "label2", "id": ref_item.id}],
            ],
        )

        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["target"]["attr"]["type"], AttrType.ARRAY_NAMED_OBJECT)
        curr = resp.json()[0]["target"]["attr"]["curr_value"]["value"]
        prev = resp.json()[0]["target"]["attr"]["prev_value"]["value"]
        self.assertEqual(len(curr), 1)
        self.assertEqual(curr[0]["name"], "label2")
        self.assertEqual(curr[0]["object"]["id"], ref_item.id)
        self.assertEqual(curr[0]["object"]["model"]["id"], ref_model.id)
        self.assertEqual(len(prev), 1)
        self.assertEqual(prev[0]["name"], "label1")
        self.assertEqual(prev[0]["object"]["id"], ref_item.id)

    def test_get_activity_has_array_group_typed_record(self):
        user = self.guest_login()
        group1 = Group.objects.create(name="ArrGroup1")
        group2 = Group.objects.create(name="ArrGroup2")
        model, item = self._setup_attr_update_activity(
            user, "arr_group_attr", AttrType.ARRAY_GROUP, [[group1.id], [group2.id]]
        )

        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["target"]["attr"]["type"], AttrType.ARRAY_GROUP)
        curr = resp.json()[0]["target"]["attr"]["curr_value"]["value"]
        prev = resp.json()[0]["target"]["attr"]["prev_value"]["value"]
        self.assertEqual(len(curr), 1)
        self.assertEqual(curr[0]["id"], group2.id)
        self.assertEqual(curr[0]["name"], group2.name)
        self.assertEqual(len(prev), 1)
        self.assertEqual(prev[0]["id"], group1.id)

    def test_get_activity_has_array_role_typed_record(self):
        user = self.guest_login()
        role1 = Role.objects.create(name="ArrRole1")
        role2 = Role.objects.create(name="ArrRole2")
        model, item = self._setup_attr_update_activity(
            user, "arr_role_attr", AttrType.ARRAY_ROLE, [[role1.id], [role2.id]]
        )

        resp = self.client.get("/user/api/v2/%s/activity" % user.id)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["target"]["attr"]["type"], AttrType.ARRAY_ROLE)
        curr = resp.json()[0]["target"]["attr"]["curr_value"]["value"]
        prev = resp.json()[0]["target"]["attr"]["prev_value"]["value"]
        self.assertEqual(len(curr), 1)
        self.assertEqual(curr[0]["id"], role2.id)
        self.assertEqual(curr[0]["name"], role2.name)
        self.assertEqual(len(prev), 1)
        self.assertEqual(prev[0]["id"], role1.id)