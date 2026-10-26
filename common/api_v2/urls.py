from django.urls import path

from . import views

urlpatterns = [
    path("import", views.CommonImportAPI.as_view()),
]
