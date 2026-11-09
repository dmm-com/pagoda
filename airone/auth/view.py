import json
from typing import Union
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.contrib.auth import views as django_auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect

from airone.lib.http import render
from airone.lib.log import Logger


@csrf_protect
def logout(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponse("Invalid HTTP method is specified", status=400)

    django_logout(request)
    return render(request, "registration/logged_out.html")


class PagodaLoginView(django_auth_views.LoginView):
    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        # Read settings per request instead of baking them into the URLconf at
        # import time, so runtime changes (and per-test overrides) are honored
        context = super().get_context_data(**kwargs)
        # getattr keeps configurations without SAML support working, and next()
        # tolerates an empty idp mapping instead of raising IndexError
        idp_mapping = getattr(settings, "SOCIAL_AUTH_SAML_ENABLED_IDPS", None)
        idp = next(iter(idp_mapping), None) if idp_mapping else None
        context.update(
            {
                "title": settings.AIRONE["TITLE"],
                "subtitle": settings.AIRONE["SUBTITLE"],
                "note_desc": settings.AIRONE["NOTE_DESC"],
                "note_link": settings.AIRONE["NOTE_LINK"],
                "sso_desc": settings.AIRONE["SSO_DESC"],
                "idp": idp,
                "password_reset_disabled": settings.AIRONE["PASSWORD_RESET_DISABLED"],
                "check_term_service": settings.AIRONE["CHECK_TERM_SERVICE"],
                "terms_of_service_url": settings.AIRONE["TERMS_OF_SERVICE_URL"],
            }
        )

        # The login page hands these values to JavaScript. They are passed as a
        # JSON payload rendered with json_script (see templates/registration/login.html)
        # so that no value is ever interpolated into a JS string literal.
        single_sign_on_login_url = None
        if idp:
            single_sign_on_login_url = "%s?%s" % (
                reverse("social:begin", args=["saml"]),
                urlencode({"idp": idp, "next": context.get("next") or ""}),
            )

        # also exposed to the legacy (non-SPA) login form
        context["single_sign_on_login_url"] = single_sign_on_login_url

        django_context: dict[str, object] = {
            "next": context.get("next") or "",
            "title": context["title"],
            "subtitle": context["subtitle"],
            "note_desc": context["note_desc"],
            "note_link": context["note_link"],
            "termsOfServiceUrl": context["terms_of_service_url"],
            "password_reset_disabled": context["password_reset_disabled"],
            "checkTermService": context["check_term_service"],
        }
        if single_sign_on_login_url is not None:
            django_context["singleSignOnLoginUrl"] = single_sign_on_login_url

        context["django_context"] = django_context

        return context

    def form_valid(self, form: AuthenticationForm) -> Union[HttpResponse, JsonResponse]:
        response = super().form_valid(form)

        if not settings.AIRONE["CHECK_TERM_SERVICE"]:
            return response

        try:
            extra_param = json.loads(self.request.POST.get("extra_param") or "")
            if extra_param.get("AGREE_TERM_OF_SERVICE"):
                response.set_cookie("AGREE_TERM_OF_SERVICE", "True")
            else:
                return JsonResponse(
                    {"error": "You have to agree to the Terms of Service to use Pagoda"}, status=400
                )

        except (json.JSONDecodeError, TypeError):
            Logger.warning(
                "Unexpected extra_param was specified from client (%s)"
                % (str(self.request.POST.get("extra_param", "")))
            )

            return JsonResponse(
                {"error": "You have to agree to the Terms of Service to use Pagoda"}, status=400
            )

        return response
