from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^attrs/([\d,]+)$", views.EntityAttrsAPI.as_view()),
]
