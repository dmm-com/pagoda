from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^set/(\d+)$", views.set_webhook, name="set_webhook"),
    re_path(r"^del/(\d+)$", views.del_webhook, name="del_webhook"),
]
