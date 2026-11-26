"""Send webhooks only to public addresses, with verified HTTPS identities."""

import ipaddress
import re
import socket
import ssl
from dataclasses import dataclass
from typing import Callable, Mapping, cast
from urllib.parse import SplitResult, urlsplit

import requests
from requests.exceptions import RequestException
from requests.models import PreparedRequest
from requests.utils import DEFAULT_CA_BUNDLE_PATH
from urllib3 import HTTPConnectionPool, HTTPSConnectionPool
from urllib3.exceptions import ConnectTimeoutError, HTTPError, NewConnectionError
from urllib3.response import HTTPResponse
from urllib3.util import Timeout

# Never let caller-supplied headers change routing or HTTP message framing.
_TRANSPORT_HEADERS = {
    "host",
    "connection",
    "content-length",
    "transfer-encoding",
    "te",
    "trailer",
    "upgrade",
    "expect",
    "proxy-authorization",
    "proxy-connection",
}
_TRANSLATION_NETWORKS = (
    ipaddress.ip_network("64:ff9b::/96"),
    ipaddress.ip_network("64:ff9b:1::/48"),
    ipaddress.ip_network("2002::/16"),
    ipaddress.ip_network("2001::/32"),
)
_HEADER_NAME = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+")


@dataclass(frozen=True)
class WebhookResponse:
    status_code: int
    reason: str

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400


def post_webhook(url: str, *, data: str, headers: Mapping[str, str]) -> WebhookResponse:
    """Resolve once and connect to a checked IP, retaining the original Host/SNI.

    A fresh direct pool avoids environment proxies, netrc credentials and shared
    connection state. Responses are closed without downloading an unbounded body.
    Redirects are failures, including redirects to other public hosts.
    """
    try:
        if any(ord(char) <= 32 or ord(char) == 127 or char == "\\" for char in url):
            raise ValueError("Invalid webhook URL")
        parsed = urlsplit(url)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or "%" in parsed.hostname
        ):
            raise ValueError("Webhook URL must be an HTTP(S) URL without credentials or scopes")
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            raise ValueError("Invalid webhook port")
        if any(
            not _HEADER_NAME.fullmatch(key) or key.lower() in _TRANSPORT_HEADERS for key in headers
        ):
            raise ValueError("Webhook headers cannot override routing or transport headers")

        # Use requests' URL/header normalization before applying the IP policy.
        prepared = requests.Request("POST", url, data=data, headers=headers).prepare()
        assert prepared.url is not None
        target = urlsplit(prepared.url)
        assert target.hostname is not None
        hostname = target.hostname
        port = target.port if target.port is not None else (443 if target.scheme == "https" else 80)
        if not 1 <= port <= 65535:
            raise ValueError("Invalid webhook port")
        addresses = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        if not addresses:
            raise ValueError("Webhook hostname has no addresses")
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if (
                not ip.is_global
                or ip.is_multicast
                or ip.is_reserved
                or (
                    isinstance(ip, ipaddress.IPv6Address)
                    and (
                        ip.ipv4_mapped is not None
                        or any(ip in network for network in _TRANSLATION_NETWORKS)
                    )
                )
            ):
                raise ValueError("Webhook destination must resolve only to public IP addresses")

        for index, address in enumerate(addresses):
            try:
                return _post_to_address(str(address[4][0]), port, target, prepared)
            except (NewConnectionError, ConnectTimeoutError):
                # Fall back only before a request could have been sent. Never
                # retry a POST after TLS, read, HTTP or other response failures.
                if index == len(addresses) - 1:
                    raise
        raise ValueError("Webhook hostname has no addresses")
    except (ValueError, OSError, HTTPError) as exc:
        # Preserve callers' verification-failure and async-job error handling.
        raise RequestException(str(exc)) from exc


def _post_to_address(
    address: str, port: int, target: SplitResult, prepared: PreparedRequest
) -> WebhookResponse:
    # The pool receives only a numeric address, so a later DNS change cannot
    # redirect this connection. TLS still authenticates the URL hostname.
    timeout = Timeout(connect=5, read=10)
    pool: HTTPConnectionPool
    if target.scheme == "https":
        assert target.hostname is not None
        hostname = target.hostname.rstrip(".")
        pool = HTTPSConnectionPool(
            address,
            port,
            timeout=timeout,
            cert_reqs=ssl.CERT_REQUIRED,
            ca_certs=DEFAULT_CA_BUNDLE_PATH,
            assert_hostname=hostname,
            server_hostname=hostname,
        )
    else:
        pool = HTTPConnectionPool(address, port, timeout=timeout)

    prepared.headers["Host"] = target.netloc
    path = target.path or "/"
    if target.query:
        path += "?" + target.query
    with pool:
        # Older urllib3 stubs omit this method's runtime annotations.
        send = cast(Callable[..., HTTPResponse], pool.urlopen)
        response = send(
            "POST",
            path,
            body=prepared.body,
            headers=prepared.headers,
            redirect=False,
            retries=False,
            preload_content=False,
        )
        try:
            if 300 <= response.status < 400:
                raise RequestException("Webhook redirects are not allowed")
            return WebhookResponse(response.status, response.reason or "")
        finally:
            response.close()
