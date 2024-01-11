from django.urls import path

from . import views

urlpatterns = [
    path(
        "",
        views.UserAPI.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path(
        "<int:pk>/",
        views.UserAPI.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "<int:pk>/edit_passwd",
        views.UserPasswordAPI.as_view(),
    ),
    path(
        "<int:pk>/su_edit_passwd",
        views.UserPasswordBySuperuserAPI.as_view(),
    ),
    path(
        "<int:pk>/auth",
        views.UserAuthAPI.as_view(),
    ),
    path(
        "token/",
        views.UserTokenAPI.as_view(
            {
                "get": "retrieve",
                "post": "refresh",
            }
        ),
    ),
    path("import/", views.UserImportAPI.as_view()),
    path("export/", views.UserExportAPI.as_view()),
    path(
        "password_reset",
        views.PasswordResetAPI.as_view(
            {
                "post": "reset",
            }
        ),
    ),
    path(
        "password_reset/confirm",
        views.PasswordResetConfirmAPI.as_view(
            {
                "post": "confirm",
            }
        ),
    ),
]
