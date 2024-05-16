from django.urls import include, re_path

from . import views

urlpatterns = [
    re_path(r"^api/v1/", include(("webhook.api_v1.urls", "webhook.api_v1"))),
    re_path(r"^(\d+)$", views.list_webhook, name="list_webhook"),
]
