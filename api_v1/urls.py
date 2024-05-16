from django.urls import include, re_path

from airone.lib.log import Logger

from . import views
from .entity.urls import urlpatterns as entity_urlpatterns
from .entry.urls import urlpatterns as entry_urlpatterns
from .job.urls import urlpatterns as job_urlpatterns
from .user import views as user_views

urlpatterns = [
    re_path(r"^user/access_token$", user_views.AccessTokenAPI.as_view()),
    re_path(r"^entity/", include(entity_urlpatterns)),
    re_path(r"^entry/", include(entry_urlpatterns)),
    re_path(r"^job/", include(job_urlpatterns)),
]

# Custom view is prioritized to handle if it exists.
try:
    from custom_view.api_v1.urls import urlpatterns as custom_patterns

    urlpatterns.append(re_path(r"^advanced/", include(custom_patterns)))
except ImportError:
    Logger.info("advanced API endpoints are unavailable")

try:
    from custom_view.api_v1 import views as custom_views

    urlpatterns.append(re_path(r"^entry$", custom_views.CustomEntryAPI.as_view()))
except ImportError:
    urlpatterns.append(re_path(r"^entry$", views.EntryAPI.as_view()))
