from django.urls import path

from . import views

urlpatterns = [path("", views.CustomAPI.as_view())]
