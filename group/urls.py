from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r"^$", views.index, name="index"),
    url(r"^api/v1/", include(("group.api_v1.urls", "group.api_v1"))),
    url(r"^api/v2/", include(("group.api_v2.urls", "group.api_v2"))),
    url(r"^edit/(\d+)$", views.edit, name="edit"),
    url(r"^do_edit/(\d+)$", views.do_edit, name="do_edit"),
    url(r"^create$", views.create, name="create"),
    url(r"^do_create$", views.do_create, name="do_create"),
    url(r"^do_delete/(\d+)$", views.do_delete, name="do_delete"),
    url(r"^export/$", views.export, name="export"),
    url(r"^import/$", views.import_user_and_group, name="import_user_and_group"),
    url(r"^do_import/$", views.do_import_user_and_group, name="do_import_user_and_group"),
]
