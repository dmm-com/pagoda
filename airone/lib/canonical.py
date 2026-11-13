"""
Build the base URL of links that leave the application (e.g. password reset
emails).

Such links must never be derived from the client-supplied Host header: with
django.contrib.sites uninstalled, get_current_site() returns a RequestSite
whose domain is request.get_host(), and with ALLOWED_HOSTS = ["*"] an
unauthenticated attacker can choose that header freely (reset-link poisoning,
CWE-640).

The host is taken from ALLOWED_HOSTS (AIRONE_ALLOWED_HOSTS) and the scheme from
SESSION_COOKIE_SECURE (AIRONE_SSL_ENABLE), both of which a production
deployment configures anyway, so no dedicated canonical-URL setting is needed.
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.http.request import split_domain_port

# Request hosts that are safe to echo back when nothing is configured: a link
# pointing at the loopback interface cannot leak a token to a third party.
_LOOPBACK_HOSTS = frozenset(["localhost", "127.0.0.1", "[::1]"])

_NO_CANONICAL_HOST = (
    "ALLOWED_HOSTS contains no concrete hostname that can drive "
    "externally-visible links (password reset emails). Set "
    "AIRONE_ALLOWED_HOSTS to the real hostnames of this deployment."
)


def _canonical_host(allowed_hosts: list[str]) -> str | None:
    """Pick the first ALLOWED_HOSTS entry usable as an absolute link host."""
    for host in allowed_hosts:
        if not host or host == "*" or host.startswith("."):
            # Wildcards cannot designate one canonical host for links.
            continue
        return host
    return None


def get_canonical_url_parts(request: HttpRequest) -> dict[str, str]:
    """
    Return site_name / domain / protocol for building externally-visible URLs.

    - The host comes from the first concrete (non-wildcard) ALLOWED_HOSTS
      entry and the scheme from SESSION_COOKIE_SECURE.
    - Without such an entry, the request host is used only when it is a
      loopback address, which keeps local development working with the default
      ALLOWED_HOSTS = ["*"].
    - Otherwise ImproperlyConfigured is raised instead of trusting the
      attacker-controlled Host header.
    """
    host = _canonical_host(list(settings.ALLOWED_HOSTS))
    if host is not None:
        return {
            "site_name": host,
            "domain": host,
            "protocol": "https" if settings.SESSION_COOKIE_SECURE else "http",
        }

    request_host = request.get_host()
    if split_domain_port(request_host)[0] not in _LOOPBACK_HOSTS:
        raise ImproperlyConfigured(_NO_CANONICAL_HOST)

    return {
        "site_name": request_host,
        "domain": request_host,
        "protocol": "https" if request.is_secure() else "http",
    }
