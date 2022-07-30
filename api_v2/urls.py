from django.urls import include, path

urlpatterns = []

try:
    urlpatterns.append(path("custom/", include("custom_view.api_v2.urls")))
except ImportError:
    pass
