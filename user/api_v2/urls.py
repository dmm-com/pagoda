from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^users$", views.list_users, name="list_users"),
    url(r"^users/(\d+)$", views.get_user, name="get_user"),
]
