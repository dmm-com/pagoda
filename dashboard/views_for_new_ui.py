from airone.lib.http import http_get, http_post
from airone.lib.http import render
from airone.lib.profile import airone_profile


@airone_profile
@http_get
def index(request):
    return render(request, 'frontend/index.html')
