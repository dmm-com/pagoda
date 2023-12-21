from django.conf.urls import include, url

urlpatterns = [
    url(r"^api/v2/", include(("trigger.api_v2.urls", "trigger.api_v2"))),
]
