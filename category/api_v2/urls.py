from django.urls import path

from . import views

urlpatterns = [
    path(
        "",
        views.CategoryAPI.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path(
        "<int:pk>/",
        views.CategoryAPI.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "delete": "destroy",
            }
        ),
    ),
]
