from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.index, name="index"),
    re_path(r"^import/$", views.import_data, name="import"),
    re_path(r"^do_import/$", views.do_import_data, name="do_import"),
    re_path(r"^advanced_search$", views.advanced_search, name="advanced_search"),
    re_path(
        r"^advanced_search_result$",
        views.advanced_search_result,
        name="advanced_search_result",
    ),
    re_path(
        r"^advanced_search_export$",
        views.export_search_result,
        name="export_search_result",
    ),
]

# If a custom view exists, the custom view has priority for viewing
try:
    from custom_view.dashboard import view as custom_view

    urlpatterns.append(re_path(r"^search/$", custom_view.search, name="search"))

except ImportError:
    urlpatterns.append(re_path(r"^search/$", views.search, name="search"))
