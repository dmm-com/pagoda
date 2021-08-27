from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^api/v1/', include(('webhook.api_v1.urls', 'webhook.api_v1'))),
    url(r'^(\d+)$', views.list_webhook, name='list_webhook'),
]
