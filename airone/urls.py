from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from api_v1.urls import urlpatterns as api_v1_urlpatterns

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='dashboard/')),
    url(r'^acl/', include(('acl.urls', 'acl'))),
    url(r'^user/', include(('user.urls', 'user'))),
    url(r'^group/', include(('group.urls', 'group'))),
    url(r'^entity/', include(('entity.urls', 'entity'))),
    url(r'^dashboard/', include(('dashboard.urls', 'dashboard'))),
    url(r'^new-ui/', include(('dashboard.urls_for_new_ui', 'dashboard_for_new_ui'))),
    url(r'^entry/', include(('entry.urls', 'entry'))),
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include(('rest_framework.urls', 'rest_framework'))),
    url(r'^api/v1/', include(api_v1_urlpatterns)),
    url(r'^job/', include(('job.urls', 'job'))),
    url(r'^auth/', include(('django.contrib.auth.urls', 'auth'))),
    url(r'^webhook/', include(('webhook.urls', 'entity'))),
]

for extension in settings.AIRONE['EXTENSIONS']:
    urlpatterns.append(url(r'^extension/%s' % extension,
                           include(('%s.urls' % extension, extension))))

urlpatterns += staticfiles_urlpatterns()
