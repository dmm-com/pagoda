from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^(?P<pk>\d+)$", views.RoleAPI.as_view({"get": "retrieve"})),
    url(r"^list$", views.RoleAPI.as_view({"get": "list"})),
]
