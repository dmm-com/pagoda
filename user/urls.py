from django.conf.urls import url

from group import views as group_views
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^edit/(\d+)$', views.edit, name='edit'),
    url(r'^do_edit/(\d+)$', views.do_edit, name='do_edit'),
    url(r'^edit_passwd/(\d+)$', views.edit_passwd, name='edit_passwd'),
    url(r'^do_edit_passwd/(\d+)$', views.do_edit_passwd, name='do_edit_passwd'),
    url(r'^do_su_edit_passwd/(\d+)$', views.do_su_edit_passwd, name='do_su_edit_passwd'),
    url(r'^create$', views.create, name='create'),
    url(r'^do_create$', views.do_create, name='do_create'),
    url(r'^do_delete/(\d+)$', views.do_delete, name='do_delete'),
    url(r'^export/$', group_views.export, name='export'),
]
