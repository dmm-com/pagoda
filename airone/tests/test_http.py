import io
import unittest
import urllib.parse

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.utils.encoding import smart_str

from acl.models import ACLBase
from airone.lib.acl import ACLType
from airone.lib.http import get_download_response, get_obj_with_check_perm, http_get
from airone.lib.test import AironeViewTest
from entry.models import Entry


class AirOneHTTPTest(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_airone_http_get_decorator(self):
        @http_get
        def mock_handler(request):
            return "mock_response"

        test_suites = [
            {"get_url": "/test", "resp_url": ["/auth/login?next=/test?"]},
            {
                "get_url": "/日本語",
                "resp_url": ["/auth/login?next=/%E6%97%A5%E6%9C%AC%E8%AA%9E?"],
            },
            {
                "get_url": "/test?query1=1&query2=test",
                "resp_url": [
                    "/auth/login?next=/test?query1%3D1%26query2%3Dtest",
                    "/auth/login?next=/test?query2%3Dtest%26query1%3D1",
                ],
            },
        ]

        for i in test_suites:
            request = self.factory.get(i["get_url"])
            request.user = AnonymousUser()

            resp = mock_handler(request)

            self.assertEqual(resp.status_code, 303)
            # Use assertIn because dict doesn't keep the key order if it's less than python 3.6
            self.assertIn(resp.url, i["resp_url"])


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()
        self.user = self.guest_login()

        self.entity = self.create_entity(self.user, "Entity", [{"name": "attr"}])
        self.entityattr = self.entity.attrs.get(name="attr")
        self.entry = self.add_entry(self.user, "Entry", self.entity, {"attr": "hoge"})
        self.attr = self.entry.attrs.get(schema=self.entityattr)

    def test_get_obj_with_check_perm(self):
        for obj in [self.entity, self.entityattr, self.entry, self.attr]:
            target_obj, error = get_obj_with_check_perm(
                self.user, obj.__class__, obj.id, ACLType.Full
            )
            self.assertEqual(target_obj, obj)
            self.assertIsNone(error)

    def test_get_obj_with_check_perm_with_invalid_param(self):
        target_obj, error = get_obj_with_check_perm(self.user, Entry, self.entity.id, ACLType.Full)
        self.assertIsNone(target_obj)
        self.assertEqual(error.content, b"Failed to get entity of specified id")
        self.assertEqual(error.status_code, 400)

    def test_get_obj_with_check_perm_without_permission(self):
        self.entry.is_public = False
        self.entry.save()

        target_obj, error = get_obj_with_check_perm(self.user, Entry, self.entry.id, ACLType.Full)
        self.assertIsNone(target_obj)
        self.assertEqual(error.content, b"You don't have permission to access this object")
        self.assertEqual(error.status_code, 400)

    def test_get_obj_with_check_perm_without_parent_permission(self):
        self.entity.default_permission = ACLType.Writable.id
        self.entity.is_public = False
        self.entity.save()

        for co_instance in [self.entityattr, self.entry, self.attr]:
            target_obj, error = get_obj_with_check_perm(
                self.user, ACLBase, co_instance.id, ACLType.Full
            )
            self.assertIsNone(target_obj)
            self.assertEqual(error.content, b"You don't have permission to access this object")
            self.assertEqual(error.status_code, 400)


class GetDownloadResponseTest(TestCase):
    def test_utf8_encoding(self):
        data = "テストデータ"
        filename = "testfile_utf8.txt"
        stream = io.StringIO(data)
        response = get_download_response(stream, filename, encode="utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, data.encode("utf-8"))
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="{urllib.parse.quote(smart_str(filename))}"',
        )
        self.assertEqual(response["Content-Type"], "application/force-download")

    def test_shift_jis_encoding_success(self):
        data = "テストデータ"  # Characters that can be represented in Shift_JIS
        filename = "testfile_sjis_ok.txt"
        stream = io.StringIO(data)
        response = get_download_response(stream, filename, encode="shift_jis")

        self.assertEqual(response.status_code, 200)
        # Compare with Shift_JIS byte string
        self.assertEqual(response.content, data.encode("shift_jis"))
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="{urllib.parse.quote(smart_str(filename))}"',
        )
        self.assertEqual(response["Content-Type"], "application/force-download")

    def test_shift_jis_encoding_error(self):
        # The full-width tilde (\uff5e) cannot be directly represented in Shift_JIS
        data = "チルダ\uff5eテスト"
        filename = "testfile_sjis_error.txt"
        stream = io.StringIO(data)

        # The response should be returned normally without error because errors='replace' is applied
        response = get_download_response(stream, filename, encode="shift_jis")

        # Verify that the response is generated normally
        self.assertEqual(response.status_code, 200)

        # Characters that cannot be encoded should be replaced
        expected_bytes = data.encode("shift_jis", errors="replace")
        self.assertEqual(response.content, expected_bytes)

        # Verify that headers are also set correctly
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="{urllib.parse.quote(smart_str(filename))}"',
        )
        self.assertEqual(response["Content-Type"], "application/force-download")
