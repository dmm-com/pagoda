from django.conf import settings

from airone.lib.test import AironeViewTest

# set test extension settings before initialization of extension is started
settings.AIRONE["EXTENSIONS"] = ["airone.tests.fixtures.example_extension1"]


class AirOneExttensionTest(AironeViewTest):
    def test_extension_request_handler(self):
        # send request to test airone extension
        resp = self.client.get("/extension/airone.tests.fixtures.example_extension1")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"test extension response")
