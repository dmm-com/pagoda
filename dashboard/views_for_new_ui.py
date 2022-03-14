from airone.lib.http import http_get
from airone.lib.http import render


@http_get
def index(request):
    return render(request, 'frontend/index.html')
