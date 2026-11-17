from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, SimpleTestCase, override_settings

from airone.lib.canonical import get_canonical_url_parts


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

    def test_loopback_request_host_is_used_without_concrete_allowed_host(self):
        for host in ("localhost:8000", "127.0.0.1:8000", "[::1]:8000", "localhost"):
            with self.subTest(host=host):
                request = self.factory.get("/", HTTP_HOST=host)
                with override_settings(ALLOWED_HOSTS=["*"]):
                    parts = get_canonical_url_parts(request)

                self.assertEqual(parts["domain"], host)
                self.assertEqual(parts["protocol"], "http")

    def test_loopback_scheme_follows_request(self):
        request = self.factory.get("/", secure=True, HTTP_HOST="localhost:8000")
        with override_settings(ALLOWED_HOSTS=["*"]):
            parts = get_canonical_url_parts(request)

        self.assertEqual(parts["protocol"], "https")

    def test_non_loopback_request_host_is_rejected(self):
        # Hosts that merely look like a loopback address must not pass either.
        for host in (
            "attacker.example",
            "localhost.attacker.example",
            "127.0.0.1.attacker.example",
        ):
            for allowed_hosts in (["*"], ["*", ".example.com"], []):
                with self.subTest(host=host, allowed_hosts=allowed_hosts):
                    request = self.factory.get("/", HTTP_HOST=host)
                    with override_settings(ALLOWED_HOSTS=["*", *allowed_hosts]):
                        with self.assertRaises(ImproperlyConfigured):
                            get_canonical_url_parts(request)
