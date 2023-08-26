from django.urls import path

from . import views

urlpatterns = [
    path(
        "<int:pk>/",
        views.JobAPI.as_view(
            {
                "get": "retrieve",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "<int:pk>/rerun",
        views.JobRerunAPI.as_view(),
    ),
    path("jobs", views.JobListAPI.as_view({"get": "list"})),
]
