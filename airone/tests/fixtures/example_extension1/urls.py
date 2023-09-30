from django.http import HttpResponse
from django.urls import re_path


def test_view_handler(request):
    return HttpResponse("test extension response")


urlpatterns = [
    re_path(r"^$", test_view_handler, name="test"),
]
