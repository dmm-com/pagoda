from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^jobs$", views.list_jobs, name="list_jobs"),
]
