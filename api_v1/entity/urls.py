from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^attrs/(?P<entity_ids>[\d,]+)$", views.EntityAttrsAPI.as_view()),
]
