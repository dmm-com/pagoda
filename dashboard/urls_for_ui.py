from django.urls import re_path

from . import views_for_ui as views

urlpatterns = [
    re_path(r"^", views.index, name="index"),
]
