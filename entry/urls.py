from django.urls import include, re_path

from acl import views as acl_views

from . import views

urlpatterns = [
    re_path(r"^(\d+)/$", views.index, name="index"),
    re_path(r"^acl/(\d+)/$", acl_views.index, name="acl"),
    re_path(r"^api/v1/", include(("entry.api_v1.urls", "entry.api_v1"))),
    re_path(r"^api/v2/", include(("entry.api_v2.urls", "entry.api_v2"))),
    re_path(r"^copy/(\d+)/$", views.copy, name="copy"),
    re_path(r"^create/(\d+)/$", views.create, name="create"),
    re_path(r"^do_copy/(\d+)$", views.do_copy, name="do_copy"),
    re_path(r"^do_create/(\d+)/$", views.do_create, name="do_create"),
    re_path(r"^do_delete/(\d+)/$", views.do_delete, name="do_delete"),
    re_path(r"^do_edit/(\d+)$", views.do_edit, name="do_edit"),
    re_path(r"^do_import/(\d+)/$", views.do_import_data, name="do_import"),
    re_path(r"^do_restore/(\d+)/$", views.do_restore, name="do_restore"),
    re_path(r"^edit/(\d+)/$", views.edit, name="edit"),
    re_path(r"^export/(\d+)/$", views.export, name="export"),
    re_path(r"^history/(\d+)/$", views.history, name="history"),
    re_path(r"^import/(\d+)/$", views.import_data, name="import"),
    re_path(r"^refer/(\d+)/$", views.refer, name="refer"),
    re_path(r"^restore/(\d+)/$", views.restore, name="restore"),
    re_path(r"^revert_attrv$", views.revert_attrv, name="revert_attrv"),
    re_path(r"^show/(\d+)/$", views.show, name="show"),
]
