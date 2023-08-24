from django.urls import path

from . import views

urlpatterns = [
    path(
        "groups",
        views.GroupAPI.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path("groups/tree", views.GroupTreeAPI.as_view({"get": "list"})),
    path("groups/import", views.GroupImportAPI.as_view()),
    path("groups/export", views.GroupExportAPI.as_view()),
    path(
        "groups/<int:pk>",
        views.GroupAPI.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "delete": "destroy",
            }
        ),
    ),
]
