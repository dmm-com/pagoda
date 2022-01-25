from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'(?P<pk>\d+)$', views.entryAPI.as_view({'get': 'retrieve'})),
    url(r'^search$', views.searchAPI.as_view({'get': 'list'}))
]
