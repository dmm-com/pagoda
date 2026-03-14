from django.http import HttpRequest, HttpResponse

from airone.lib.http import http_get, render


@http_get
def index(request: HttpRequest) -> HttpResponse:
    return render(request, "frontend/index.html")
