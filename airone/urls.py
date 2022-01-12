from django.conf import settings
from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from api_v1.urls import urlpatterns as api_v1_urlpatterns
from airone.auth import view as auth_view

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='dashboard/')),
    url(r'^acl/', include(('acl.urls', 'acl'))),
    url(r'^user/', include(('user.urls', 'user'))),
    url(r'^group/', include(('group.urls', 'group'))),
    url(r'^entity/', include(('entity.urls', 'entity'))),
    url(r'^dashboard/', include(('dashboard.urls', 'dashboard'))),
    url(r'^new-ui/', include(('dashboard.urls_for_new_ui', 'dashboard_for_new_ui'))),
    url(r'^entry/', include(('entry.urls', 'entry'))),
    url(r'^api/v1/', include(api_v1_urlpatterns)),
    url(r'^job/', include(('job.urls', 'job'))),
    url(r'^auth/login/', auth_views.LoginView.as_view(
        redirect_authenticated_user=True,
    ), name='login'),
    url(r'^auth/logout/', auth_view.logout, name='logout'),
    url(r'^webhook/', include(('webhook.urls', 'webhook'))),
    # url(r'^__debug__/', include('debug_toolbar.urls')),
]

for extension in settings.AIRONE['EXTENSIONS']:
    urlpatterns.append(url(r'^extension/%s' % extension,
                           include(('%s.urls' % extension, extension))))

urlpatterns += staticfiles_urlpatterns()
