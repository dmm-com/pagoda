from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect


def index(request: HttpRequest) -> HttpResponseRedirect:
    return redirect("ui/")
