from django.conf.urls import url, include

from airone.lib.log import Logger
from group import views as group_views
from user import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^api/v2/', include('user.api_v2.urls')),
    url(r'^edit/(\d+)$', views.edit, name='edit'),
    url(r'^do_edit/(\d+)$', views.do_edit, name='do_edit'),
    url(r'^edit_passwd/(\d+)$', views.edit_passwd, name='edit_passwd'),
    url(r'^do_edit_passwd/(\d+)$', views.do_edit_passwd, name='do_edit_passwd'),
    url(r'^do_su_edit_passwd/(\d+)$', views.do_su_edit_passwd, name='do_su_edit_passwd'),
    url(r'^create$', views.create, name='create'),
    url(r'^do_create$', views.do_create, name='do_create'),
    url(r'^do_delete/(\d+)$', views.do_delete, name='do_delete'),
    url(r'^export/$', group_views.export, name='export'),
    url(r'^password_reset/$', views.PasswordReset.as_view(), name='password_reset'),
    url(r'^password_reset/done/$', views.PasswordResetDone.as_view(), name='password_reset_done'),
    url(r'^reset/(?P<uidb64>.+)/(?P<token>.+)/$',
        views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    url(r'^reset/done/$', views.PasswordResetComplete.as_view(), name='password_reset_complete'),
]

try:
    from custom_view.user.urls import override_urlpatterns

    urlpatterns = override_urlpatterns(urlpatterns)
except ImportError:
    Logger.info("There is no URL dispatcher of custom-view")
