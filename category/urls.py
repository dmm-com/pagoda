from django.urls import include, re_path

urlpatterns = [
    re_path(r"^api/v2/", include(("category.api_v2.urls", "category.api_v2"))),
]
