from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^get/(\d+)$', views.get_webhook, name='get_webhook'),
]
