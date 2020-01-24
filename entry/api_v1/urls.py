from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^get_referrals/(\d+)/$', views.get_referrals, name='get_referrals'),
    url(r'^get_entries/([\d,]+)/$', views.get_entries, name='get_entries'),
    url(r'^search_entries/([\d,]+)$', views.search_entries, name='search_entries'),
    url(r'^get_attr_referrals/(\d+)/$', views.get_attr_referrals, name='get_attr_referrals'),
    url(r'^get_entry_history/(\d+)/$', views.get_entry_history, name='get_entry_history'),
    url(r'^get_entry_info/(\d+)$', views.get_entry_info, name='get_entry_info'),
]
