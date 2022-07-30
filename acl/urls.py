from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r"^(\d+)/$", views.index, name="index"),
    url(r"^api/v2/", include(("acl.api_v2.urls", "acl.api_v2"))),
    url(r"^set$", views.set, name="set"),
]
