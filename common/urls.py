from django.urls import include, re_path

urlpatterns = [
    re_path(r"^api/v2/", include(("common.api_v2.urls", "common.api_v2"))),
]
