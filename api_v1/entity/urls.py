from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^attrs/([\d,]+)$", views.EntityAttrsAPI.as_view()),
]
