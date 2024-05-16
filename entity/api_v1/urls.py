from django.urls import re_path

from entity.api_v1 import views

urlpatterns = [
    re_path(r"^get_entities$", views.get_entities, name="get_entities"),
]
