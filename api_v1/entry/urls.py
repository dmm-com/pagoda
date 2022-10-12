from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^search$", views.EntrySearchAPI.as_view()),
    url(r"^search_chain$", views.EntrySearchChainAPI.as_view()),
    url(r"^referral$", views.EntryReferredAPI.as_view()),
    url(r"^update_history$", views.UpdateHistory.as_view()),
]
