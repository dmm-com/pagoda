from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, SimpleTestCase, override_settings

from airone.lib.canonical import get_canonical_url_parts, is_valid_base_url


class CanonicalUrlPartsTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    def test_host_derived_from_allowed_hosts_ignores_client_header(self):
        # The client-controlled Host header must never leak into links.
        self.request.META["HTTP_HOST"] = "attacker.example"
        with override_settings(ALLOWED_HOSTS=["pagoda.example.com"], SESSION_COOKIE_SECURE=True):
            parts = get_canonical_url_parts(self.request)

        self.assertEqual(parts["domain"], "pagoda.example.com")
        self.assertEqual(parts["site_name"], "pagoda.example.com")
        self.assertEqual(parts["protocol"], "https")

    def test_scheme_follows_session_cookie_secure(self):
        with override_settings(ALLOWED_HOSTS=["pagoda.example.com"], SESSION_COOKIE_SECURE=False):
            parts = get_canonical_url_parts(self.request)

        self.assertEqual(parts["protocol"], "http")

    def test_host_port_is_preserved(self):
        with override_settings(
            ALLOWED_HOSTS=["pagoda.example.com:8080"], SESSION_COOKIE_SECURE=False
        ):
            parts = get_canonical_url_parts(self.request)

        self.assertEqual(parts["domain"], "pagoda.example.com:8080")

    def test_wildcard_entries_are_skipped(self):
        with override_settings(
            ALLOWED_HOSTS=["*", ".example.com", "pagoda.example.com"],
            SESSION_COOKIE_SECURE=False,
        ):
            parts = get_canonical_url_parts(self.request)

        self.assertEqual(parts["domain"], "pagoda.example.com")

    def test_fallback_uses_request_host(self):
        self.request.META["HTTP_HOST"] = "localhost:8000"
        with override_settings(ALLOWED_HOSTS=["*"], CANONICAL_URL_FALLBACK=True):
            parts = get_canonical_url_parts(self.request)

        self.assertEqual(parts["domain"], "localhost:8000")
        self.assertEqual(parts["protocol"], "http")

    def test_no_fallback_in_production(self):
        self.request.META["HTTP_HOST"] = "attacker.example"
        with override_settings(ALLOWED_HOSTS=["*"], CANONICAL_URL_FALLBACK=False):
            with self.assertRaises(ImproperlyConfigured):
                get_canonical_url_parts(self.request)

    def test_no_fallback_when_only_wildcards_configured(self):
        self.request.META["HTTP_HOST"] = "attacker.example"
        with override_settings(ALLOWED_HOSTS=["*", ".example.com"], CANONICAL_URL_FALLBACK=False):
            with self.assertRaises(ImproperlyConfigured):
                get_canonical_url_parts(self.request)

    def test_use_https_for_fallback(self):
        self.request = self.factory.get("/", secure=True)
        with override_settings(ALLOWED_HOSTS=["*"], CANONICAL_URL_FALLBACK=True):
            parts = get_canonical_url_parts(self.request, use_https=True)

        self.assertEqual(parts["protocol"], "https")


class IsValidBaseUrlTest(SimpleTestCase):
    def test_accepts_absolute_base_urls(self):
        for valid in (
            "https://pagoda.example.com",
            "http://pagoda.example.com",
            "pagoda.example.com",
            "https://pagoda.example.com:8080",
        ):
            with self.subTest(base_url=valid):
                self.assertTrue(is_valid_base_url(valid))

    def test_rejects_url_extras_and_userinfo(self):
        for invalid in (
            "",
            "pagoda.example.com/path",
            "javascript://x",
            "://",
            "https://user:password@pagoda.example.com",
            "https://pagoda.example.com?a=1",
            "https://pagoda.example.com/#fragment",
        ):
            with self.subTest(base_url=invalid):
                self.assertFalse(is_valid_base_url(invalid))
