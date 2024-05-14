from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^search$", views.EntrySearchAPI.as_view()),
    re_path(r"^search_chain$", views.EntrySearchChainAPI.as_view()),
    re_path(r"^referral$", views.EntryReferredAPI.as_view()),
    re_path(r"^update_history$", views.UpdateHistory.as_view()),
]
