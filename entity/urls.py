from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^create$', views.create, name='create'),
    url(r'^do_create$', views.do_create, name='do_create'),
    url(r'^edit/(\d+)$', views.edit, name='edit'),
    url(r'^do_edit/(\d+)$', views.do_edit, name='do_edit'),
    url(r'^settings/(\d+)$', views.settings, name='settings'),
    url(r'^export/$', views.export, name='export'),
    url(r'^dashboard/(\d+)$', views.dashboard, name='dashboard'),
    url(r'^dashboard/config/(\d+)$', views.conf_dashboard, name='conf_dashboard'),
    url(r'^dashboard/config/register/(\d+)$', views.do_conf_dashboard, name='do_conf_dashboard'),
    url(r'^do_delete/(\d+)$', views.do_delete, name='do_delete'),
    url(r'^history/(\d+)$', views.history, name='history'),
    url(r'^api/v1/', include(('entity.api_v1.urls', 'entity.api_v1'))),
    url(r'^auth/', include('django.contrib.auth.urls')),
]
