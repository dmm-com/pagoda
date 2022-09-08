from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
    url(r"^users$", views.UserListAPI.as_view()),
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
