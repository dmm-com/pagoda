"""
URL patterns for Hello World Plugin API endpoints
"""

from django.urls import path

from . import views

urlpatterns = [
    path("hello/", views.HelloView.as_view(), name="hello"),
    path("greet/<str:name>/", views.GreetView.as_view(), name="greet"),
    path("status/", views.StatusView.as_view(), name="status"),
    path("test/", views.TestView.as_view(), name="test"),  # For authentication-free testing
]
