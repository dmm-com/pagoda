from django.conf.urls import url, include

from . import views
from acl import views as acl_views

urlpatterns = [
    url(r'^(\d+)/$', views.index, name='index'),
    url(r'^acl/(\d+)/$', acl_views.index, name='acl'),
    url(r'^api/v1/', include('entry.api_v1.urls', namespace='entry.api_v1', app_name='api_v1')),
    url(r'^copy/(\d+)/$', views.copy, name='copy'),
    url(r'^create/(\d+)/$', views.create, name='create'),
    url(r'^do_copy/(\d+)$', views.do_copy, name='do_copy'),
    url(r'^do_create/(\d+)/$', views.do_create, name='do_create'),
    url(r'^do_delete/(\d+)/$', views.do_delete, name='do_delete'),
    url(r'^do_edit/(\d+)$', views.do_edit, name='do_edit'),
    url(r'^do_import/(\d+)/$', views.do_import_data, name='do_import'),
    url(r'^do_restore/(\d+)/$', views.do_restore, name='do_restore'),
    url(r'^edit/(\d+)/$', views.edit, name='edit'),
    url(r'^export/(\d+)/$', views.export, name='export'),
    url(r'^history/(\d+)/$', views.history, name='history'),
    url(r'^import/(\d+)/$', views.import_data, name='import'),
    url(r'^refer/(\d+)/$', views.refer, name='refer'),
    url(r'^restore/(\d+)/$', views.restore, name='restore'),
    url(r'^revert_attrv$', views.revert_attrv, name='revert_attrv'),
    url(r'^show/(\d+)/$', views.show, name='show'),
]
