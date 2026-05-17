from django.conf import settings
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from multidb.pinning import this_thread_is_pinned, unpin_this_thread

from airone.lib.multidb import AironePinningRouterMiddleware, db_readonly
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


class AironePinningRouterMiddlewareTest(SimpleTestCase):
    """Unit tests for the @db_readonly override."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AironePinningRouterMiddleware(get_response=lambda r: HttpResponse())
        unpin_this_thread()

    def tearDown(self):
        unpin_this_thread()

    def _plain_view(self, request):
        return HttpResponse()

    def _decorated_view_func(self):
        @db_readonly
        def view(request):
            return HttpResponse()

        return view

    def _decorated_drf_view(self):
        @db_readonly
        class View:
            pass

        # DRF attaches the view class to view_func via .cls
        def view_func(request):
            return HttpResponse()

        view_func.cls = View
        return view_func

    def test_post_without_marker_pins_thread_and_sets_cookie(self):
        request = self.factory.post("/foo/")
        self.middleware.process_request(request)
        self.assertTrue(this_thread_is_pinned())

        self.middleware.process_view(request, self._plain_view, [], {})
        # Plain view does not opt in; pin remains.
        self.assertTrue(this_thread_is_pinned())

        response = self.middleware.process_response(request, HttpResponse())
        self.assertIn(COOKIE_NAME, response.cookies)

    def test_post_with_function_marker_unpins_and_skips_cookie(self):
        request = self.factory.post("/foo/")
        self.middleware.process_request(request)
        self.assertTrue(this_thread_is_pinned())

        view = self._decorated_view_func()
        self.middleware.process_view(request, view, [], {})
        self.assertFalse(this_thread_is_pinned())
        self.assertTrue(getattr(request, "_airone_db_readonly", False))

        response = self.middleware.process_response(request, HttpResponse())
        self.assertNotIn(COOKIE_NAME, response.cookies)

    def test_post_with_drf_class_marker_unpins_and_skips_cookie(self):
        request = self.factory.post("/foo/")
        self.middleware.process_request(request)
        self.assertTrue(this_thread_is_pinned())

        view_func = self._decorated_drf_view()
        self.middleware.process_view(request, view_func, [], {})
        self.assertFalse(this_thread_is_pinned())

        response = self.middleware.process_response(request, HttpResponse())
        self.assertNotIn(COOKIE_NAME, response.cookies)

    def test_get_does_not_pin_regardless_of_marker(self):
        request = self.factory.get("/foo/")
        self.middleware.process_request(request)
        self.assertFalse(this_thread_is_pinned())

        response = self.middleware.process_response(request, HttpResponse())
        self.assertNotIn(COOKIE_NAME, response.cookies)

    def test_explicit_db_write_response_wins_over_marker(self):
        """response._db_write=True must always set the cookie, even on a marked view."""
        request = self.factory.post("/foo/")
        self.middleware.process_request(request)
        view = self._decorated_view_func()
        self.middleware.process_view(request, view, [], {})

        response = HttpResponse()
        response._db_write = True
        response = self.middleware.process_response(request, response)
        self.assertIn(COOKIE_NAME, response.cookies)
