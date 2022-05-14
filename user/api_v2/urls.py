from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^users$", views.UserListAPI.as_view()),
    url(r"^users/(?P<pk>\d+)$", views.UserRetrieveAPI.as_view()),
]
