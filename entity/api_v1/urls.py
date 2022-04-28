from django.conf.urls import url

from entity.api_v1 import views

urlpatterns = [
    url(r"^get_entities$", views.get_entities, name="get_entities"),
]
