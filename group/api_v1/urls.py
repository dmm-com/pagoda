from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^groups/tree$", views.GroupTreeAPI.as_view()),
]
