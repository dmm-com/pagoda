from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r"^$", views.index, name="index"),
    url(r"^api/v2/", include(("job.api_v2.urls", "job.api_v2"))),
    url(r"^download/(\d+)$", views.download, name="download"),
]
