from django.urls import path

from . import views

urlpatterns = [
    path(
        "advanced_search/",
        views.AdvancedSearchAPI.as_view({"get": "list"}),
    ),
]
