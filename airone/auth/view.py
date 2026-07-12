import json
from typing import Union

from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.contrib.auth import views as django_auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest, HttpResponse, JsonResponse
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
        context.update(
            {
                "title": settings.AIRONE["TITLE"],
                "subtitle": settings.AIRONE["SUBTITLE"],
                "note_desc": settings.AIRONE["NOTE_DESC"],
                "note_link": settings.AIRONE["NOTE_LINK"],
                "sso_desc": settings.AIRONE["SSO_DESC"],
                "idp": list(getattr(settings, "SOCIAL_AUTH_SAML_ENABLED_IDPS").keys())[0]
                if hasattr(settings, "SOCIAL_AUTH_SAML_ENABLED_IDPS")
                else None,
                "password_reset_disabled": settings.AIRONE["PASSWORD_RESET_DISABLED"],
                "check_term_service": settings.AIRONE["CHECK_TERM_SERVICE"],
                "terms_of_service_url": settings.AIRONE["TERMS_OF_SERVICE_URL"],
            }
        )
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
