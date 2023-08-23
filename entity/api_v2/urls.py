from django.urls import path

from . import views

urlpatterns = [
    path("history/<int:pk>", views.history, name="history"),
    path(
        "",
        views.EntityAPI.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path(
        "import",
        views.EntityImportAPI.as_view(),
    ),
    path(
        "export",
        views.EntityExportAPI.as_view(),
    ),
    path(
        "attrs",
        views.EntityAttrNameAPI.as_view(),
    ),
    path(
        "<int:pk>/",
        views.EntityAPI.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "<int:entity_id>/entries/",
        views.EntityEntryAPI.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path(
        "<int:entity_id>/histories/",
        views.EntityHistoryAPI.as_view(
            {
                "get": "list",
            }
        ),
    ),
]
