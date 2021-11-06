from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^acls/(?P<pk>\d+)$', views.ACLAPI.as_view({'get': 'retrieve'})),
]
