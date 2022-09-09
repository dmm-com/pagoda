from django.urls import path

from . import views

urlpatterns = [
    path("", views.UserListAPI.as_view()),
    path(
        "<int:pk>/",
        views.UserAPI.as_view(
            {
                "get": "retrieve",
                "delete": "destroy",
            }
        ),
    ),
]
