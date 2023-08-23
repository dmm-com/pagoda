from django.urls import path

from . import views

urlpatterns = [
    path(
        "<int:pk>",
        views.RoleAPI.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "",
        views.RoleAPI.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path(
        "import",
        views.RoleImportAPI.as_view(),
    ),
    path(
        "export",
        views.RoleExportAPI.as_view(),
    ),
]
