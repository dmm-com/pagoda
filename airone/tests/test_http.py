import unittest

from airone.lib.http import http_get
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory


class AirOneHTTPTest(unittest.TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_airone_http_get_decorator(self):

        @http_get
        def mock_handler(request):
            return 'mock_response'

        test_suites = [
            {'get_url': '/test', 'resp_url': '/dashboard/login?next=/test?'},
            {'get_url': '/日本語', 'resp_url': '/dashboard/login?next=/%E6%97%A5%E6%9C%AC%E8%AA%9E?'},
            {'get_url': '/test?query1=1&query2=test',
             'resp_url': '/dashboard/login?next=/test?query1%3D1%26query2%3Dtest'},
        ]

        for i in test_suites:
            request = self.factory.get(i['get_url'])
            request.user = AnonymousUser()

            resp = mock_handler(request)

            self.assertEqual(resp.status_code, 303)
            self.assertEqual(resp.url, i['resp_url'])
