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
        "<int:pk>/referral/",
        views.EntryReferralAPI.as_view(
            {
                "get": "list",
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
        "<int:pk>/copy/",
        views.EntryAPI.as_view(
            {
                "post": "copy",
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
    path(
        "<int:entity_id>/export/",
        views.EntryExportAPI.as_view(),
    ),
]
