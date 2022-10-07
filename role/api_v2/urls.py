from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^(?P<pk>\d+)$", views.RoleAPI.as_view({
        "get": "retrieve",
        "put": "update",
        "delete": "destroy",
    })),
    url(r"^$", views.RoleAPI.as_view({
        "get": "list",
        "post": "create",
    })),
]
