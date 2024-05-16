from django.urls import include, re_path

from group import views as group_views
from user import views

urlpatterns = [
    re_path(r"^$", views.index, name="index"),
    re_path(r"^api/v2/", include(("user.api_v2.urls", "user.api_v2"))),
    re_path(r"^edit/(\d+)$", views.edit, name="edit"),
    re_path(r"^do_edit/(\d+)$", views.do_edit, name="do_edit"),
    re_path(r"^edit_passwd/(\d+)$", views.edit_passwd, name="edit_passwd"),
    re_path(r"^do_edit_passwd/(\d+)$", views.do_edit_passwd, name="do_edit_passwd"),
    re_path(r"^do_su_edit_passwd/(\d+)$", views.do_su_edit_passwd, name="do_su_edit_passwd"),
    re_path(r"^create$", views.create, name="create"),
    re_path(r"^do_create$", views.do_create, name="do_create"),
    re_path(r"^do_delete/(\d+)$", views.do_delete, name="do_delete"),
    re_path(r"^change_ldap_auth$", views.change_ldap_auth, name="change_ldap_auth"),
    re_path(r"^export/$", group_views.export, name="export"),
    re_path(r"^password_reset/$", views.PasswordReset.as_view(), name="password_reset"),
    re_path(
        r"^password_reset/done/$",
        views.PasswordResetDone.as_view(),
        name="password_reset_done",
    ),
    re_path(
        r"^reset/(?P<uidb64>.+)/(?P<token>.+)/$",
        views.PasswordResetConfirm.as_view(),
        name="password_reset_confirm",
    ),
    re_path(
        r"^reset/done/$",
        views.PasswordResetComplete.as_view(),
        name="password_reset_complete",
    ),
]
