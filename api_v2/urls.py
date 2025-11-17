from django.conf import settings
from django.urls import include, path

from airone.lib.log import Logger

urlpatterns = []

try:
    urlpatterns.append(path("custom/", include("custom_view.api_v2.urls")))
except ImportError as e:
    Logger.warning(e)

# Conditionally add plugin API v2 patterns
if settings.AIRONE.get("PLUGINS", {}).get("ENABLED", False):
    try:
        from airone.plugins.integration import plugin_integration

        urlpatterns.extend(plugin_integration.get_api_v2_patterns())
    except ImportError as e:
        Logger.warning(f"Plugin system not available: {e}")
