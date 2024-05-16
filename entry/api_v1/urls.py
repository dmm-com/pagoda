from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^get_referrals/(\d+)/$", views.get_referrals, name="get_referrals"),
    re_path(r"^get_entries/([\d,]+)/$", views.get_entries, name="get_entries"),
    re_path(r"^search_entries/([\d,]+)$", views.search_entries, name="search_entries"),
    re_path(
        r"^get_attr_referrals/(\d+)/$",
        views.get_attr_referrals,
        name="get_attr_referrals",
    ),
    re_path(r"^get_entry_history/(\d+)/$", views.get_entry_history, name="get_entry_history"),
    re_path(r"^get_entry_info/(\d+)$", views.get_entry_info, name="get_entry_info"),
    re_path(r"^create_entry_attr/(\d+)$", views.create_entry_attr, name="create_entry_attr"),
]
