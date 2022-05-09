from django.conf.urls import url

from . import views_for_new_ui as views

urlpatterns = [
    url(r"^", views.index, name="index"),
]
