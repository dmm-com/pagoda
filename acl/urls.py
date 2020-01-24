from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(\d+)/$', views.index, name='index'),
    url(r'^set$', views.set, name='set'),
]
