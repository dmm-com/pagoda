from django.urls import path

from . import views

urlpatterns = [
    path(
        "<int:pk>/",
        views.EntryAPI.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "<int:pk>/restore/",
        views.EntryAPI.as_view(
            {
                "post": "restore",
            }
        ),
    ),
    path(
        "search/",
        views.searchAPI.as_view(
            {
                "get": "list",
            }
        ),
    ),
]
