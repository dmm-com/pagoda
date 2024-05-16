from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^tree$", views.GroupTreeAPI.as_view()),
]
