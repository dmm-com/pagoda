from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^tree$", views.GroupTreeAPI.as_view()),
]
