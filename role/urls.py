from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^create/$', views.create, name='create'),
    url(r'^do_create/$', views.do_create, name='do_create'),
    url(r'^edit/(\d+)/$', views.edit, name='edit'),
    url(r'^do_edit/(\d+)/$', views.do_edit, name='do_edit'),
]
