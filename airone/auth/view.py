from django.contrib.auth import logout as django_logout
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse

from airone.lib.http import render


@csrf_protect
def logout(request):
    if request.method != "POST":
        return HttpResponse("Invalid HTTP method is specified", status=400)

    django_logout(request)
    return render(request, "registration/logged_out.html")
