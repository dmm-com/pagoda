from django.urls import include, path

from airone.lib.log import Logger

urlpatterns = []

try:
    urlpatterns.append(path("custom/", include("custom_view.api_v2.urls")))
except ImportError as e:
    Logger.error(e)
