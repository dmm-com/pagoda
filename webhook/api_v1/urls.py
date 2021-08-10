from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^set/(\d+)$', views.set_webhook, name='set_webhook'),
    url(r'^del/(\d+)$', views.del_webhook, name='del_webhook'),
]
