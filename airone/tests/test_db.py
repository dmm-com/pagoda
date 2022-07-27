import time

import django
from django.utils.http import parse_http_date

from airone.lib.test import AironeViewTest

COOKIE_NAME = django.conf.settings.REPLICATED_FORCE_MASTER_COOKIE_NAME


class ViewTest(AironeViewTest):
    def setUp(self):
        super(ViewTest, self).setUp()

        self.admin = self.admin_login()

    def test_replicated_middleware(self):
        # Post: use master, set cookie
        with self.assertLogs("django_replicated.router", level="DEBUG") as log:
            self.assertNotIn(COOKIE_NAME, self.client.cookies)
            response = self.client.post("/dashboard/")
            self.assertEqual(response.cookies[COOKIE_NAME].value, "true")
            self.assertIn("DEBUG:django_replicated.router:db_for_write: default", log.output)

        # First GET after POST: use master, set cookie
        with self.assertLogs("django_replicated.router", level="DEBUG") as log:
            self.assertEqual(self.client.cookies[COOKIE_NAME].value, "true")
            response = self.client.get("/dashboard/")
            self.assertEqual(response.cookies[COOKIE_NAME].value, "true")
            self.assertIn("DEBUG:django_replicated.router:db_for_write: default", log.output)

        # Second GET after POST: use master, set cookie
        with self.assertLogs("django_replicated.router", level="DEBUG") as log:
            self.assertEqual(response.cookies[COOKIE_NAME].value, "true")
            response = self.client.get("/dashboard/")
            self.assertEqual(response.cookies[COOKIE_NAME].value, "true")
            self.assertIn("DEBUG:django_replicated.router:db_for_write: default", log.output)

        # GET after expired cookies: use slave
        with self.assertLogs("django_replicated.router", level="DEBUG") as log:
            self.assertTrue(
                parse_http_date(self.client.cookies[COOKIE_NAME]["expires"])
                < (time.time() + django.conf.settings.REPLICATED_FORCE_MASTER_COOKIE_MAX_AGE)
            )
            # Delete expired cookies
            del self.client.cookies[COOKIE_NAME]
            response = self.client.get("/dashboard/")
            self.assertNotIn(COOKIE_NAME, self.client.cookies)
            self.assertIn("DEBUG:django_replicated.router:db_for_read: default", log.output)
