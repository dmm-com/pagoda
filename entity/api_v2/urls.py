from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
    url(r"^history/(\d+)$", views.history, name="history"),
    path(
        "",
        views.EntityAPI.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path(
        "<int:pk>/",
        views.EntityAPI.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "<int:entity_id>/entries/",
        views.EntityEntryAPI.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path(
        "<int:entity_id>/histories/",
        views.EntityHistoryAPI.as_view(
            {
                "get": "list",
            }
        ),
    ),
]
