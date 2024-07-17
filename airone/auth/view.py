import json

from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.contrib.auth import views as django_auth_views
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_protect

from airone.lib.http import render
from airone.lib.log import Logger


@csrf_protect
def logout(request):
    if request.method != "POST":
        return HttpResponse("Invalid HTTP method is specified", status=400)

    django_logout(request)
    return render(request, "registration/logged_out.html")


class PagodaLoginView(django_auth_views.LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)

        if not settings.AIRONE["CHECK_TERM_SERVICE"]:
            return response

        try:
            extra_param = json.loads(self.request.POST.get("extra_param"))
            if extra_param.get("AGREE_TERM_OF_SERVICE"):
                response.set_cookie("AGREE_TERM_OF_SERVICE", True)
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
