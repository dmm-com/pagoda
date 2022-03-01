from django.urls import path
from django.conf.urls import url

from . import views

urlpatterns = [
    path('entries/<int:entity_id>', views.entryAPI.as_view({'get': 'list'})),
    url(r'(?P<pk>\d+)$', views.entryWithAttrAPI.as_view({'get': 'retrieve'})),
    url(r'^search$', views.searchAPI.as_view({'get': 'list'}))
]
