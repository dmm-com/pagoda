from django.urls import path

from . import views

urlpatterns = [
    path(
        "<int:pk>/",
        views.EntryAPI.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "<int:pk>/referral/",
        views.EntryReferralAPI.as_view(
            {
                "get": "list",
            }
        ),
    ),
    path(
        "<int:pk>/restore/",
        views.EntryAPI.as_view(
            {
                "post": "restore",
            }
        ),
    ),
    path(
        "<int:pk>/copy/",
        views.EntryAPI.as_view(
            {
                "post": "copy",
            }
        ),
    ),
    path(
        "<int:pk>/histories/",
        views.EntryAPI.as_view(
            {
                "get": "histories",
            }
        ),
    ),
    path(
        "search/",
        views.searchAPI.as_view(
            {
                "get": "list",
            }
        ),
    ),
    path(
        "advanced_search_result_export/",
        views.AdvancedSearchResultAPI.as_view(),
    ),
    path(
        "<int:entity_id>/export/",
        views.EntryExportAPI.as_view(),
    ),
    path(
        "<int:attr_id>/attr_referrals/",
        views.EntryAttrReferralsAPI.as_view(
            {
                "get": "list",
            }
        ),
    ),
    path(
        "<int:pk>/attrv_restore/",
        views.EntryAttributeValueRestoreAPI.as_view(),
    ),
    path("advanced_search/", views.AdvancedSearchAPI.as_view()),
    path("import/", views.EntryImportAPI.as_view()),
]
