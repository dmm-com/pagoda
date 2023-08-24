from django.urls import path

from acl.api_v2 import views

urlpatterns = [
    path(
        "acls/<int:pk>",
        views.ACLAPI.as_view({"get": "retrieve", "put": "update"}),
    ),
    path(
        "acls/<int:pk>/history",
        views.ACLHistoryAPI.as_view(),
    ),
]
