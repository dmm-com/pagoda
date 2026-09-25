from collections.abc import Callable
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin


class IframePolicyMiddleware(MiddlewareMixin):
    """Allow configured origins to frame the UI and login while protecting other routes."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        super().__init__(get_response)
        self.origins = []
        for value in settings.IFRAME_ALLOWED_ORIGINS:
            origin = value.strip()
            if not origin:
                continue
            try:
                parsed = urlsplit(origin)
                valid = (
                    parsed.scheme in ("https", "http")
                    and parsed.hostname
                    and not parsed.username
                    and not parsed.password
                    and not parsed.path
                    and not parsed.query
                    and not parsed.fragment
                    and parsed.port != 0
                    and not any(char.isspace() or char in "*;,\\\"'" for char in origin)
                )
            except ValueError:
                valid = False
            if not valid:
                raise ImproperlyConfigured(
                    "AIRONE_IFRAME_ALLOWED_ORIGINS must contain HTTP(S) origins "
                    "without paths, wildcards, or credentials."
                )
            self.origins.append(origin)

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        allowed_path = request.path_info.startswith("/ui/") or request.path_info in (
            "/auth/login",
            "/auth/login/",
        )
        if not self.origins or not allowed_path:
            return response

        policy = "frame-ancestors " + " ".join(self.origins)
        existing = response.get("Content-Security-Policy")
        # Multiple CSP policies are enforced together, preserving existing restrictions.
        response["Content-Security-Policy"] = f"{existing}, {policy}" if existing else policy
        if "X-Frame-Options" in response:
            del response["X-Frame-Options"]
        return response
