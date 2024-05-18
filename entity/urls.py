from django.urls import include, re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.index, name="index"),
    re_path(r"^create$", views.create, name="create"),
    re_path(r"^do_create$", views.do_create, name="do_create"),
    re_path(r"^edit/(\d+)$", views.edit, name="edit"),
    re_path(r"^do_edit/(\d+)$", views.do_edit, name="do_edit"),
    re_path(r"^export/$", views.export, name="export"),
    re_path(r"^dashboard/(\d+)$", views.dashboard, name="dashboard"),
    re_path(r"^dashboard/config/(\d+)$", views.conf_dashboard, name="conf_dashboard"),
    re_path(
        r"^dashboard/config/register/(\d+)$",
        views.do_conf_dashboard,
        name="do_conf_dashboard",
    ),
    re_path(r"^do_delete/(\d+)$", views.do_delete, name="do_delete"),
    re_path(r"^history/(\d+)$", views.history, name="history"),
    re_path(r"^api/v1/", include(("entity.api_v1.urls", "entity.api_v1"))),
    re_path(r"^api/v2/", include(("entity.api_v2.urls", "entity.api_v2"))),
]
