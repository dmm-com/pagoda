from django.urls import path

from . import views

urlpatterns = [
    path(
        "<int:pk>",
        views.TriggerAPI.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "",
        views.TriggerAPI.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
]
