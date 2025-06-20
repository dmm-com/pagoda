import re
from typing import Callable

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse


class URLGateKeeper:
    """
    This middleware will be activated when LEGACY_UI_DISABLED and never guide
    legacy page even through user intentionally send it.
    """

    VEILED_URL_PATTERNS = [
        ## Advanced Search
        r"^/dashboard/import$",
        r"^/dashboard/do_import$",
        r"^/dashboard/advanced_search$",
        r"^/dashboard/advanced_search_result$",
        r"^/dashboard/advanced_search_export$",
        ## User
        r"^/user/reset.*$",
        r"^/user/password_reset/$",
        r"^/user/change_ldap_auth/$",
        r"^/user/do_.*$",
        ## group:
        r"^/group/do_.*$",
        ## role:
        r"^/role/do_.*$",
        ## Model
        r"^/entity/do_.*$",
        ## Item
        r"^/entry/do_.*$",
        r"^/entry/import/.*$",
        r"^/entry/api/v1/.*$",
        ## APIv1
        r"^/api/v1/.*$",
    ]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if settings.AIRONE.get("LEGACY_UI_DISABLED"):
            if any(re.match(x, request.path) for x in self.VEILED_URL_PATTERNS):
                raise Http404

        return self.get_response(request)
