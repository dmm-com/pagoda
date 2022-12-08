from airone.lib.http import http_get, render


@http_get
def index(request):
    return render(request, "frontend/index.html")
