from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
    path(
        "<int:pk>/",
        views.JobAPI.as_view(
            {
                "get": "retrieve",
            }
        ),
    ),
    url(r"^jobs$", views.JobListAPI.as_view({"get": "list"})),
]
