from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.JobAPI.as_view()),
    url(r'^run/(\d+)$', views.SpecificJobAPI.as_view()),
    url(r'^search$', views.SearchJob.as_view()),
]
