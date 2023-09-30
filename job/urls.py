from django.urls import include, re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.index, name="index"),
    re_path(r"^api/v2/", include(("job.api_v2.urls", "job.api_v2"))),
    re_path(r"^download/(\d+)$", views.download, name="download"),
]
