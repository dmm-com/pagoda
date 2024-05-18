from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.JobAPI.as_view()),
    re_path(r"^run/(\d+)$", views.SpecificJobAPI.as_view()),
    re_path(r"^search$", views.SearchJob.as_view()),
]
