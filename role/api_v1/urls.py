from django.urls import path
from django.conf.urls import url

from . import views

urlpatterns = [
    path('<int:role_id>/', views.RoleAPI.as_view()),
]
