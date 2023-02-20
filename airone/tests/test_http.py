import unittest

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from airone.lib.acl import ACLType
from airone.lib.http import get_obj_with_check_perm, http_get
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
