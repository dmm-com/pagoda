from django.urls import path

from . import views

urlpatterns = [
    path('<int:role_id>/', views.RoleAPI.as_view()),
]
