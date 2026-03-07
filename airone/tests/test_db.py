from django.conf import settings

from airone.lib.test import AironeViewTest

COOKIE_NAME = settings.MULTIDB_PINNING_COOKIE


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        self.admin = self.admin_login()

    def test_pinning_middleware_sets_cookie_on_post(self):
        """POST request should set the pinning cookie."""
        self.assertNotIn(COOKIE_NAME, self.client.cookies)
        response = self.client.post("/dashboard/")
        self.assertEqual(response.cookies[COOKIE_NAME].value, "y")

    def test_pinning_middleware_keeps_cookie_on_get_after_post(self):
        """GET request with existing pinning cookie should work normally."""
        self.client.post("/dashboard/")
        self.assertEqual(self.client.cookies[COOKIE_NAME].value, "y")

        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

    def test_pinning_middleware_no_cookie_on_plain_get(self):
        """GET request without prior write should not set pinning cookie."""
        self.assertNotIn(COOKIE_NAME, self.client.cookies)
        response = self.client.get("/dashboard/")
        self.assertNotIn(COOKIE_NAME, response.cookies)
