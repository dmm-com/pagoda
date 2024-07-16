from django.conf import settings
from django.http import HttpResponseNotFound

from airone.lib.http import HttpResponseSeeOther, http_get, render


@http_get
def index(request):
    return render(request, "frontend/index.html")


def error404(request, exception):
    if not request.user.is_authenticated:
        if settings.AIRONE.get("LEGACY_UI_DISABLED"):
            return HttpResponseSeeOther("/auth/login/?next=/ui/")
        return HttpResponseSeeOther("/auth/login/")
    return HttpResponseNotFound(render(request, "frontend/index.html"))
