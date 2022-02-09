from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^history/(\d+)$', views.history, name='history'),
    url(r'^(?P<pk>\d+)$', views.GetEntity.as_view({'get': 'retrieve'})),
]
