from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
    url(r"^jobs$", views.list_jobs, name="list_jobs"),
    path(
        "<int:pk>/",
        views.JobAPI.as_view(
            {
                "get": "retrieve",
            }
        ),
    ),
]
