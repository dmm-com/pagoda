from django.urls import path

from . import views

urlpatterns = [
    path(
        "",
        views.UserAPI.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path(
        "<int:pk>/",
        views.UserAPI.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "token/",
        views.UserTokenAPI.as_view(
            {
                "get": "retrieve",
                "post": "refresh",
            }
        ),
    ),
]
