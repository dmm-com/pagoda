from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^groups$", views.GroupAPI.as_view({"get": "list"})),
    url(r"^groups/(?P<pk>\d+)$", views.GroupAPI.as_view({"get": "retrieve"})),
]
