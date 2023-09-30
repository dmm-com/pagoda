from django.urls import include, re_path

from . import views

urlpatterns = [
    re_path(r"^(\d+)/$", views.index, name="index"),
    re_path(r"^api/v2/", include(("acl.api_v2.urls", "acl.api_v2"))),
    re_path(r"^set$", views.set, name="set"),
]
