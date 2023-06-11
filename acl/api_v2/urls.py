from django.conf.urls import url

from acl.api_v2 import views

urlpatterns = [
    url(
        r"^acls/(?P<pk>\d+)$",
        views.ACLAPI.as_view({"get": "retrieve", "put": "update"}),
    ),
    url(
        r"^acls/(?P<pk>\d+)/history$",
        views.ACLHistoryAPI.as_view({"get": "get"}),
    ),
]
