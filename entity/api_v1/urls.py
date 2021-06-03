from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^get_entities$', views.get_entities, name='get_entities'),
]
