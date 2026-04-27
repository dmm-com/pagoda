import json
from unittest import mock
from unittest.mock import Mock, patch

import yaml
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.authtoken.models import Token
from rest_framework import status

from airone.lib.test import AironeViewTest, with_airone_settings
from airone.lib.types import (
    AttrType,
)
from group.models import Group
from user.models import User
from entry import tasks as entry_tasks
from entry.models import Entry, AliasEntry


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
        DAIMYO_NAMES = ["松永久秀", "織田信長", "豊臣秀吉"]
        daimyos = {x: self._create_user(x) for x in DAIMYO_NAMES}
        model_prefecture = self.create_entity(
            user_guest,
            "都道府県",
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
                "大阪府",
                "京都府",
                "徳島県",
                "奈良県",
                "滋賀県",
                "岐阜県",
                "愛知県",
                "静岡県",
                "東京都",
                "福井県",
                "岡山県",
                "埼玉県",
                "長野県",
                "神奈川県",
                "山梨県",
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
                ("筒井城", "奈良県"),
                ("一乗谷城", "福井県"),
                ("備中高松城", "岡山県"),
            ]
        }

        # change ruler of Kyoto prefecture over the course of history
        # attr_ruler_of_kyoto = item_prefectures["京都府"].attrs.get(name="ruler")
        attr_ruler_of_kyoto = model_prefecture.attrs.get(name="ruler")
        for daimyo_name in DAIMYO_NAMES:
            # create each castles by specified daimyos
            self.client.login(username=daimyo_name, password=daimyo_name)
            params = {
                "name": item_prefectures["京都府"].name,
                "attrs": [
                    {"id": attr_ruler_of_kyoto.id, "value": daimyo_name},
                ],
            }
            resp = self.client.put(
                "/entry/api/v2/%s/" % item_prefectures["京都府"].id,
                json.dumps(params),
                "application/json",
            )
            self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # record each castle by each daimyos
        attr_location_of_castle = model_castle.attrs.get(name="location")
        attr_designer_of_castle = model_castle.attrs.get(name="designer")
        for daimyo_name, castle_name, location_name, designer_name in [
            ("松永久秀", "多聞山城", "奈良県", ""),
            ("織田信長", "安土城", "滋賀県", "丹羽長秀"),
            ("豊臣秀吉", "大坂城", "大阪府", "黒田官兵衛"),
        ]:
            # create each castles by specified daimyos
            self.client.login(username=daimyo_name, password=daimyo_name)

            # send API request to create castle item
            params = {
                "name": castle_name,
                "attrs": [
                    {"id": attr_location_of_castle.id, "value": item_prefectures[location_name].id},
                    {"id": attr_designer_of_castle.id, "value": item_prefectures[designer_name].id},
                ],
            }
            resp = self.client.post(
                "/entity/api/v2/%s/entries/" % model_castle.id,
                json.dumps(params),
                "application/json",
            )
            self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # destroy cassles by each daimyos
        for daimyo_name, castle_name, location_name in [
            ("松永久秀", "筒井城", "奈良県"),
            ("織田信長", "一乗谷城", "福井県"),
            ("豊臣秀吉", "備中高松城", "岡山県"),
        ]:
            # create each castles by specified daimyos
            self.client.login(username=daimyo_name, password=daimyo_name)

            # send API request to delete castle item
            item_cassle = Entry.objects.filter(name=castle_name, model=model_castle).first()
            resp = self.client.delete(
                "/entry/api/v2/%s/" % item_cassle.id, None, "application/json"
            )
            self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Here is the main processing of this test case
        TGT_USERNAME = "織田信長"
        self.client.login(username=TGT_USERNAME, password=TGT_USERNAME)

        # call API to get recent activity of target user
        resp = self.client.get("/user/api/v2/%s/activity" % self.guest_login().id)
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
                    "value": "updated_value",
                }
                "model": {
                    "id": 10,
                    "name": "model name",
                },
            },
            "timestamp": "2024-01-01T00:00:00Z",
        }
        """
        # last activity is deleting castle by 織田信長, so check it first
        self.assertEqual(resp.json()[0]["action_type"], "delete")
        self.assertEqual(resp.json()[0]["target_type"], "item")
        self.assertEqual(resp.json()[0]["target"]["id"], item_castles["一乗谷城"].id)
        self.assertEqual(resp.json()[0]["target"]["model"]["id"], model_castle.id)

        # before that target user update attribute of created Item
        self.assertEqual(resp.json()[1]["action_type"], "udpate")
        self.assertEqual(resp.json()[1]["target_type"], "item")
        self.assertEqual(resp.json()[1]["target"]["id"], item_castles["安土城"].id)
        self.assertEqual(resp.json()[1]["target"]["attr"]["name"], "location")
        self.assertEqual(resp.json()[1]["target"]["attr"]["value"], item_prefectures["滋賀県"].id)
        self.assertEqual(resp.json()[1]["target"]["model"]["id"], model_castle.id)

        # before that target user update another attribute of created Item
        self.assertEqual(resp.json()[2]["action_type"], "udpate")
        self.assertEqual(resp.json()[2]["target_type"], "item")
        self.assertEqual(resp.json()[2]["target"]["id"], item_castles["安土城"].id)
        self.assertEqual(resp.json()[2]["target"]["attr"]["name"], "designer")
        self.assertEqual(resp.json()[2]["target"]["attr"]["value"], "丹羽長秀")
        self.assertEqual(resp.json()[2]["target"]["model"]["id"], model_castle.id)

        # before that target user create castle item
        self.assertEqual(resp.json()[3]["action_type"], "create")
        self.assertEqual(resp.json()[3]["target_type"], "item")
        self.assertEqual(resp.json()[3]["target"]["id"], item_castles["安土城"].id)
        self.assertEqual(resp.json()[3]["target"]["model"]["id"], model_castle.id)

        # before that target user update attribute of prefecture item
        self.assertEqual(resp.json()[4]["action_type"], "udpate")
        self.assertEqual(resp.json()[4]["target_type"], "item")
        self.assertEqual(resp.json()[4]["target"]["id"], item_prefectures["京都府"].id)
        self.assertEqual(resp.json()[4]["target"]["attr"]["name"], "ruler")
        self.assertEqual(resp.json()[4]["target"]["attr"]["value"], "織田信長")
        self.assertEqual(resp.json()[4]["target"]["model"]["id"], model_prefecture.id)
