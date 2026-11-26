import io
import socket
import ssl
from unittest import mock

from django.test import SimpleTestCase
from requests.exceptions import RequestException
from urllib3.exceptions import ConnectTimeoutError, NewConnectionError, ReadTimeoutError, SSLError

from airone.lib.webhook import post_webhook


def dns_answer(*addresses):
    return [
        (socket.AF_INET6 if ":" in ip else socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))
        for ip in addresses
    ]


class WebhookTransportTest(SimpleTestCase):
    def setUp(self):
        self.dns = self.enterContext(mock.patch("airone.lib.webhook.socket.getaddrinfo"))
        self.dns.return_value = dns_answer("93.184.216.34")
        self.http = self.enterContext(mock.patch("airone.lib.webhook.HTTPConnectionPool"))
        self.https = self.enterContext(mock.patch("airone.lib.webhook.HTTPSConnectionPool"))
        self.pool = self.https.return_value
        self.response = self.pool.urlopen.return_value
        self.response.status = 200
        self.response.reason = "OK"

    def test_public_https_preserves_identity_payload_and_authentication(self):
        response = post_webhook(
            "https://example.com:8443/hook?event=x",
            data='{"event": "entry.create"}',
            headers={"Authorization": "Bearer test-only", "Content-Type": "application/json"},
        )
        self.assertTrue(response.ok)
        self.dns.assert_called_once_with("example.com", 8443, type=socket.SOCK_STREAM)
        args, kwargs = self.https.call_args
        self.assertEqual(args, ("93.184.216.34", 8443))
        self.assertEqual(kwargs["cert_reqs"], ssl.CERT_REQUIRED)
        self.assertEqual(kwargs["server_hostname"], "example.com")
        self.assertEqual(kwargs["assert_hostname"], "example.com")
        self.assertTrue(kwargs["ca_certs"])
        self.assertEqual(kwargs["timeout"].connect_timeout, 5)
        self.assertEqual(kwargs["timeout"].read_timeout, 10)
        args, kwargs = self.pool.urlopen.call_args
        self.assertEqual(args, ("POST", "/hook?event=x"))
        self.assertEqual(kwargs["body"], '{"event": "entry.create"}')
        self.assertEqual(kwargs["headers"]["Host"], "example.com:8443")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-only")
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        self.assertFalse(kwargs["redirect"])
        self.assertFalse(kwargs["retries"])
        self.assertFalse(kwargs["preload_content"])
        self.response.close.assert_called_once()

    def test_public_http_and_ipv6_remain_supported(self):
        self.dns.return_value = dns_answer("2606:4700:4700::1111")
        pool = self.http.return_value
        pool.urlopen.return_value.status = 204
        pool.urlopen.return_value.reason = "No Content"
        response = post_webhook("http://[2606:4700:4700::1111]/", data="{}", headers={})
        self.assertTrue(response.ok)
        self.assertEqual(self.http.call_args.args, ("2606:4700:4700::1111", 80))
        self.assertEqual(pool.urlopen.call_args.kwargs["headers"]["Host"], "[2606:4700:4700::1111]")
        self.https.assert_not_called()

    def test_non_public_and_transition_addresses_never_open_a_pool(self):
        for ip in (
            "127.0.0.1",
            "0.0.0.0",
            "10.0.0.1",
            "172.16.0.1",
            "192.168.0.1",
            "169.254.169.254",
            "100.64.0.1",
            "192.0.2.1",
            "224.0.0.1",
            "255.255.255.255",
            "::",
            "::1",
            "fc00::1",
            "fe80::1",
            "ff02::1",
            "2001:db8::1",
            "::ffff:127.0.0.1",
            "::ffff:8.8.8.8",
            "64:ff9b::a9fe:a9fe",
            "64:ff9b:1::a00:1",
            "2002:7f00:1::",
            "2001::1",
        ):
            with self.subTest(ip=ip):
                self.dns.return_value = dns_answer(ip)
                with self.assertRaises(RequestException):
                    post_webhook("https://example.com/", data="{}", headers={})
        self.http.assert_not_called()
        self.https.assert_not_called()

    def test_mixed_dns_answers_are_rejected_regardless_of_order(self):
        for addresses in (("93.184.216.34", "::1"), ("127.0.0.1", "93.184.216.34")):
            with self.subTest(addresses=addresses):
                self.dns.return_value = dns_answer(*addresses)
                with self.assertRaises(RequestException):
                    post_webhook("https://example.com/", data="{}", headers={})
        self.https.assert_not_called()

    def test_dns_change_after_verification_does_not_change_the_connection_target(self):
        self.dns.side_effect = [dns_answer("93.184.216.34"), dns_answer("127.0.0.1")]
        post_webhook("https://example.com/", data="{}", headers={})
        self.assertEqual(self.dns.call_count, 1)
        self.assertEqual(self.https.call_args.args[0], "93.184.216.34")
        with self.assertRaises(RequestException):
            post_webhook("https://example.com/", data="{}", headers={})
        self.assertEqual(self.https.call_count, 1)

    def test_ambiguous_or_non_http_urls_fail_before_dns(self):
        for url in (
            "file:///etc/passwd",
            "ftp://example.com/",
            "//example.com/",
            "https://",
            "https://user:password@example.com/",
            "https://example.com\\@127.0.0.1/",
            "https://[fe80::1%25eth0]/",
            "https://%31%32%37.0.0.1/",
            "https://example.com:bad/",
            "https://example.com:0/",
            "https://example.com\r\n/",
            " https://example.com/",
        ):
            with self.subTest(url=url), self.assertRaises(RequestException):
                post_webhook(url, data="{}", headers={})
        self.dns.assert_not_called()
        self.http.assert_not_called()
        self.https.assert_not_called()

    def test_alternative_loopback_encodings_are_checked_after_resolution(self):
        self.dns.return_value = dns_answer("127.0.0.1")
        for url in ("http://2130706433/", "http://0x7f000001/", "http://0177.0.0.1/"):
            with self.subTest(url=url), self.assertRaises(RequestException):
                post_webhook(url, data="{}", headers={})
        self.http.assert_not_called()

    def test_transport_headers_and_header_injection_are_rejected(self):
        for headers in (
            {"hOsT": "metadata.google.internal"},
            {"Host ": "metadata.google.internal"},
            {"Host\t": "metadata.google.internal"},
            {"Content-Length": "0"},
            {"Transfer-Encoding": "chunked"},
            {"Connection": "upgrade"},
            {"Proxy-Authorization": "test"},
            {"X-Test": "test\r\nHost: localhost"},
        ):
            with self.subTest(headers=headers), self.assertRaises(RequestException):
                post_webhook("https://example.com/", data="{}", headers=headers)
        self.dns.assert_not_called()

    def test_redirects_are_failures_without_a_second_request(self):
        for status in (301, 302, 303, 307, 308):
            with self.subTest(status=status):
                self.response.status = status
                self.response.headers = {"Location": "http://169.254.169.254/"}
                with self.assertRaisesRegex(RequestException, "redirects"):
                    post_webhook("https://example.com/", data="{}", headers={})
        self.assertEqual(self.pool.urlopen.call_count, 5)
        self.assertEqual(self.response.close.call_count, 5)

    def test_tls_timeout_dns_and_http_errors_preserve_failure_semantics(self):
        for error in (
            SSLError("certificate verify failed"),
            ReadTimeoutError(None, "/", "timeout"),
        ):
            with self.subTest(error=error), self.assertRaises(RequestException):
                self.pool.urlopen.side_effect = error
                post_webhook("https://example.com/", data="{}", headers={})
        for result in ([], socket.gaierror("DNS lookup failed")):
            self.dns.side_effect = result if isinstance(result, Exception) else None
            self.dns.return_value = result
            with self.subTest(result=result), self.assertRaises(RequestException):
                post_webhook("https://example.com/", data="{}", headers={})
        self.dns.side_effect = None
        self.dns.return_value = dns_answer("93.184.216.34")
        self.pool.urlopen.side_effect = None
        self.response.status = 403
        self.response.reason = "Forbidden"
        response = post_webhook("https://example.com/", data="{}", headers={})
        self.assertFalse(response.ok)
        self.assertEqual(response.reason, "Forbidden")

    @mock.patch.dict("os.environ", {"HTTPS_PROXY": "http://127.0.0.1:8080"})
    @mock.patch("requests.Session", side_effect=AssertionError("Must not consult environment"))
    def test_environment_cannot_supply_proxies_or_implicit_credentials(self, session):
        post_webhook("https://example.com/", data="{}", headers={})
        session.assert_not_called()
        self.assertEqual(self.https.call_args.args[0], "93.184.216.34")

    def test_only_connect_failures_fall_back_to_other_checked_public_addresses(self):
        self.dns.return_value = dns_answer("2606:4700:4700::1111", "93.184.216.34")
        for error in (NewConnectionError(None, "unreachable"), ConnectTimeoutError("timeout")):
            with self.subTest(error=error):
                self.https.reset_mock()
                self.pool.urlopen.side_effect = [error, self.response]
                self.assertTrue(post_webhook("https://example.com/", data="{}", headers={}).ok)
                self.assertEqual(
                    [call.args[0] for call in self.https.call_args_list],
                    ["2606:4700:4700::1111", "93.184.216.34"],
                )
        for error in (
            SSLError("certificate verify failed"),
            ReadTimeoutError(None, "/", "timeout"),
        ):
            with self.subTest(error=error):
                self.https.reset_mock()
                self.pool.urlopen.side_effect = error
                with self.assertRaises(RequestException):
                    post_webhook("https://example.com/", data="{}", headers={})
                self.assertEqual(self.https.call_count, 1)

    def test_absolute_dns_name_keeps_certificate_validation_compatible(self):
        post_webhook("https://example.com./", data="{}", headers={})
        self.assertEqual(self.https.call_args.kwargs["server_hostname"], "example.com")
        self.assertEqual(self.https.call_args.kwargs["assert_hostname"], "example.com")


class WebhookConnectionTest(SimpleTestCase):
    def test_real_pool_connects_to_numeric_ip_and_preserves_http_host(self):
        for scheme in ("http", "https"):
            with self.subTest(scheme=scheme):
                sock = mock.Mock()
                sock.makefile.return_value = io.BytesIO(
                    b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
                )
                with (
                    mock.patch("airone.lib.webhook.socket.getaddrinfo") as dns,
                    mock.patch(
                        "urllib3.util.connection.create_connection", return_value=sock
                    ) as tcp,
                    mock.patch("urllib3.connection._ssl_wrap_socket_and_match_hostname") as tls,
                ):
                    dns.return_value = dns_answer("93.184.216.34")
                    tls.return_value = (sock, True)
                    response = post_webhook(f"{scheme}://example.com/hook", data="{}", headers={})
                self.assertTrue(response.ok)
                self.assertEqual(tcp.call_args.args[0][0], "93.184.216.34")
                self.assertEqual(dns.call_count, 1)
                sent = b"".join(call.args[0] for call in sock.sendall.call_args_list)
                self.assertIn(b"POST /hook HTTP/1.1\r\n", sent)
                self.assertIn(b"Host: example.com\r\n", sent)
                self.assertTrue(sent.endswith(b"{}"))
                if scheme == "https":
                    self.assertEqual(tls.call_args.kwargs["server_hostname"], "example.com")
                    self.assertEqual(tls.call_args.kwargs["assert_hostname"], "example.com")
                    self.assertEqual(tls.call_args.kwargs["cert_reqs"], ssl.CERT_REQUIRED)
                else:
                    tls.assert_not_called()
