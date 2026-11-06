from django.urls import path

from . import views

urlpatterns = [
    path("<int:pk>/histories/", views.RoleAPI.as_view({"get": "histories"})),
    path("<int:pk>/restore/", views.RoleAPI.as_view({"post": "restore"})),
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
