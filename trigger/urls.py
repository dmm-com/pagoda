from django.conf.urls import include
from django.urls import re_path

urlpatterns = [
    re_path(r"^api/v2/", include(("trigger.api_v2.urls", "trigger.api_v2"))),
]
