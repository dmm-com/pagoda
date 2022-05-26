from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
    url(r"^history/(\d+)$", views.history, name="history"),
    url(
        r"^entities$",
        views.EntityAPI.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    url(r"^entities/(?P<pk>\d+)$", views.EntityAPI.as_view({"get": "retrieve"})),
    path(
        "<int:entity_id>/entries/",
        views.EntityEntryAPI.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
]
