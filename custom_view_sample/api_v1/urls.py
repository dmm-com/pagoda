from django.urls import path

from . import views

urlpatterns = [path("", views.CustomEntryAPI.as_view())]
