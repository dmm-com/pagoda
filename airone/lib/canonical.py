"""
Utilities to build externally-visible base URLs.

Links that are sent outside of the application (e.g. password reset emails)
must never be derived from the client-supplied Host header. With
django.contrib.sites uninstalled, get_current_site() returns a RequestSite
whose domain is simply request.get_host(), and with an unrestricted
ALLOWED_HOSTS an unauthenticated attacker can choose that header freely
(reset-link poisoning, CWE-640).

Use get_canonical_url_parts() whenever you need site_name / domain / protocol
for such links. The values come from settings that production deployments
configure anyway (AIRONE_ALLOWED_HOSTS / AIRONE_SSL_ENABLE), so no dedicated
canonical-URL setting is required.

Design note: Django's standard infrastructure for a single source of truth
domain is the django.contrib.sites framework (DB-backed Site row + SITE_ID).
Pagoda does not enable it, and that route would add a migration plus
per-deployment DB seeding of the Site record. The ALLOWED_HOSTS derivation
above was chosen instead: it reuses one setting production already must
configure and still never trusts the request. If upstream later adopts the
sites framework, only the host/scheme source inside
get_canonical_url_parts() needs swapping; the call-site contract
(site_name / domain / protocol) and the "never derive from request.get_host()"
guarantee stay unchanged.
"""

from typing import Any
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

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


def get_canonical_url_parts(request: HttpRequest, use_https: bool = False) -> dict[str, Any]:
    """
    Return site_name / domain / protocol for building externally-visible URLs.

    - The host comes from the first concrete (non-wildcard) ALLOWED_HOSTS
      entry, the scheme from SESSION_COOKIE_SECURE (which AIRONE_SSL_ENABLE
      already drives). Only concrete settings already used in production are
      involved.
    - When no such entry exists and CANONICAL_URL_FALLBACK is enabled
      (development only), the values fall back to get_current_site(request).
    - Otherwise, raise ImproperlyConfigured instead of trusting the
      attacker-controlled Host header.
    """
    host = _canonical_host(list(getattr(settings, "ALLOWED_HOSTS", []) or []))
    if host is not None:
        return {
            "site_name": host,
            "domain": host,
            "protocol": "https" if getattr(settings, "SESSION_COOKIE_SECURE", False) else "http",
        }

    if not getattr(settings, "CANONICAL_URL_FALLBACK", False):
        raise ImproperlyConfigured(_NO_CANONICAL_HOST)

    # Development fallback: use the request host. This branch must not be
    # reachable in production (see CANONICAL_URL_FALLBACK).
    site = get_current_site(request)
    return {
        "site_name": site.name,
        "domain": site.domain,
        "protocol": "https" if use_https else "http",
    }


def is_valid_base_url(base_url: str) -> bool:
    """Whether `base_url` is an absolute http(s) base URL without extras.

    Kept as a small helper for tests and tooling that validate a canonical
    URL string (scheme and host only; no user info, query or fragment).
    """
    if not base_url:
        return False
    # Accept values without an explicit scheme by defaulting to https.
    # Note: urlsplit() normalizes the scheme to lowercase, but keeps
    # userinfo (user:pass@) inside netloc, so check it explicitly.
    parts = urlsplit(base_url if "://" in base_url else f"https://{base_url}")
    has_valid_path = parts.path in ("", "/")
    has_no_extras = not (parts.query or parts.fragment)
    has_no_userinfo = not (parts.username or parts.password)
    return all(
        (
            parts.scheme in ("http", "https"),
            bool(parts.netloc),
            has_valid_path,
            has_no_extras,
            has_no_userinfo,
        )
    )
