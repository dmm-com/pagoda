from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^history/(\d+)$', views.history, name='history'),
    url(r'^entities$', views.EntityAPI.as_view({'get': 'list'})),
    url(r'^entities/(?P<pk>\d+)$', views.EntityAPI.as_view({'get': 'retrieve'})),
]
