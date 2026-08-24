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
        "<int:pk>/download",
        views.JobAPI.as_view(
            {
                "get": "download",
            }
        ),
    ),
    path(
        "<int:pk>/preview",
        views.JobAPI.as_view(
            {
                "get": "preview",
            }
        ),
    ),
    path(
        "<int:pk>/preview/download",
        views.JobAPI.as_view(
            {
                "get": "preview_download",
            }
        ),
    ),
    path("jobs", views.JobListAPI.as_view({"get": "list"})),
]
