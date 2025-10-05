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
    # Entity endpoints - demonstrating model access through SDK
    path("entities/", views.EntityListView.as_view(), name="entity-list"),
    path("entities/<int:entity_id>/", views.EntityDetailView.as_view(), name="entity-detail"),
    # Entry endpoints - demonstrating entry model with attributes
    path("entries/", views.EntryListView.as_view(), name="entry-list"),
    path("entries/<int:entry_id>/", views.EntryDetailView.as_view(), name="entry-detail"),
]
