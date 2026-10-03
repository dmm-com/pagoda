from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.middleware.clickjacking import XFrameOptionsMiddleware
from django.test import RequestFactory, SimpleTestCase, override_settings

from airone.middleware.iframe import IframePolicyMiddleware


@override_settings(IFRAME_ALLOWED_ORIGINS=[], X_FRAME_OPTIONS="DENY")
class IframePolicyTest(SimpleTestCase):
    def response(self, path, headers=None):
        middleware = IframePolicyMiddleware(
            XFrameOptionsMiddleware(lambda request: HttpResponse(headers=headers))
        )
        return middleware(RequestFactory().get(path))

    def test_disabled_by_default(self):
        for path in ("/ui/", "/auth/login", "/auth/login/"):
            with self.subTest(path=path):
                response = self.response(path)
                self.assertEqual(response["X-Frame-Options"], "DENY")
                self.assertNotIn("Content-Security-Policy", response)

    @override_settings(
        IFRAME_ALLOWED_ORIGINS=["https://confl.example.com", "https://wiki.test:8443"]
    )
    def test_multiple_origins_and_route_boundary(self):
        for path in (
            "/ui/",
            "/ui/entities/1/entries/",
            "/ui/?query=test",
            "/auth/login",
            "/auth/login/",
            "/auth/login/?next=/ui/",
        ):
            with self.subTest(path=path):
                response = self.response(path, {"X-Frame-Options": "DENY"})
                self.assertNotIn("X-Frame-Options", response)
                self.assertEqual(
                    response["Content-Security-Policy"],
                    "frame-ancestors https://confl.example.com https://wiki.test:8443",
                )
        for path in (
            "/ui",
            "/ui-other/",
            "/auth/login/extra",
            "/auth/login-other",
            "/auth/logout/",
            "/auth/sso/",
            "/entity/api/v2/",
            "/",
        ):
            with self.subTest(path=path):
                response = self.response(path)
                self.assertEqual(response["X-Frame-Options"], "DENY")
                self.assertNotIn("Content-Security-Policy", response)

    @override_settings(IFRAME_ALLOWED_ORIGINS=["https://confl.example.com"])
    def test_preserves_existing_csp(self):
        existing = "default-src 'self'; frame-ancestors 'none'"
        response = self.response("/ui/", {"Content-Security-Policy": existing})
        self.assertEqual(
            response["Content-Security-Policy"],
            existing + ", frame-ancestors https://confl.example.com",
        )

    def test_invalid_origins_fail_closed(self):
        for origin in (
            "*",
            "https://*.test",
            "https://test/path",
            "https://test;",
            "null",
            "https://user:pass@test",
            "https://te\nst",
            "https://test:bad",
        ):
            with self.subTest(origin=origin), override_settings(IFRAME_ALLOWED_ORIGINS=[origin]):
                with self.assertRaises(ImproperlyConfigured):
                    self.response("/ui/")

    @override_settings(IFRAME_ALLOWED_ORIGINS=["", "  "])
    def test_empty_values_do_not_enable_framing(self):
        self.assertEqual(self.response("/ui/")["X-Frame-Options"], "DENY")

    def test_disabled_custom_middleware_preserves_response(self):
        response = HttpResponse(headers={"X-Frame-Options": "SAMEORIGIN"})
        middleware = IframePolicyMiddleware(lambda request: response)
        result = middleware(RequestFactory().get("/ui/"))
        self.assertIs(result, response)
        self.assertEqual(result["X-Frame-Options"], "SAMEORIGIN")
