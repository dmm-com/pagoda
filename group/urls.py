from django.urls import include, re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.index, name="index"),
    re_path(r"^api/v1/", include(("group.api_v1.urls", "group.api_v1"))),
    re_path(r"^api/v2/", include(("group.api_v2.urls", "group.api_v2"))),
    re_path(r"^edit/(\d+)$", views.edit, name="edit"),
    re_path(r"^do_edit/(\d+)$", views.do_edit, name="do_edit"),
    re_path(r"^create$", views.create, name="create"),
    re_path(r"^do_create$", views.do_create, name="do_create"),
    re_path(r"^do_delete/(\d+)$", views.do_delete, name="do_delete"),
    re_path(r"^export/$", views.export, name="export"),
    re_path(r"^import/$", views.import_user_and_group, name="import_user_and_group"),
    re_path(r"^do_import/$", views.do_import_user_and_group, name="do_import_user_and_group"),
]
