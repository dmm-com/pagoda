import mock
import unittest

from airone.lib.profile import airone_profile
from django.conf import settings
from django.http.request import HttpRequest


class AirOneProfilerTest(unittest.TestCase):

    def setUp(self):
        # this saves original configurations to be able to retrieve them
        self.orig_conf_profile = settings.AIRONE['ENABLE_PROFILE']

        # this enables do profiling
        settings.AIRONE['ENABLE_PROFILE'] = True

    def tearDown(self):
        # this retrieves original configurations
        settings.AIRONE['ENABLE_PROFILE'] = self.orig_conf_profile

    def test_airone_profile_decorator(self):
        # Initialize mock request objects
        mock_user = mock.Mock()
        mock_user.id = 1234

        mock_request = mock.Mock(spec=HttpRequest)
        mock_request.method = 'GET'
        mock_request.path = '/test'
        mock_request.user = mock_user

        @airone_profile
        def mock_handler(request):
            return 'mock_response'

        # This captures log output via logger and store output message to the log variable
        with self.assertLogs('airone', level='INFO') as log:
            # call mocked http request handler which decorate airone_profile
            mock_handler(mock_request)

        # This checks wether logger output a message as expected
        self.assertEqual(len(log.output), 1)
        self.assertRegex(log.output[0],
                         r'\(Profiling result: 0.[0-9]+s\) \(user-id: 1234\) GET /test$')
