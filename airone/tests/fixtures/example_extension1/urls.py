from django.conf.urls import url
from django.http import HttpResponse


def test_view_handler(request):
    return HttpResponse("test extension response")


urlpatterns = [
    url(r"^$", test_view_handler, name="test"),
]
