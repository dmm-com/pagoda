import logging
from typing import Any, List

from django.conf import settings

from .discovery import discover_plugins
from .registry import plugin_registry

logger = logging.getLogger(__name__)


class PluginIntegration:
    """Plugin Django integration management

    Provides functionality to integrate the plugin system with Django applications.
    Manages dynamic handling of INSTALLED_APPS, URL patterns, and API v2 patterns.
    """

    def __init__(self):
        self.initialized = False

    def is_plugins_enabled(self) -> bool:
        """Check if plugins are enabled

        Automatically enabled if any plugins are specified in ENABLED_PLUGINS.
        Default is False (disabled).

        Returns:
            True if plugins are enabled
        """
        enabled_plugins = getattr(settings, "ENABLED_PLUGINS", [])
        return bool(enabled_plugins)

    def initialize(self):
        """Initialize the plugin system

        Only executes plugin auto-discovery if plugins are enabled.
        """
        if not self.initialized and self.is_plugins_enabled():
            logger.info("Initializing plugin system...")
            discover_plugins()
            self._inject_models()
            self._load_override_config()
            self.initialized = True
            logger.info("Plugin system initialized successfully")

    def _load_override_config(self):
        """Load override registrations from BACKEND_PLUGIN_ENTITY_OVERRIDES config."""
        try:
            from .override_manager import override_registry

            # Get BACKEND_PLUGIN_ENTITY_OVERRIDES from AIRONE settings
            airone_settings = getattr(settings, "AIRONE", {})
            override_config = airone_settings.get("BACKEND_PLUGIN_ENTITY_OVERRIDES", {})

            if not override_config:
                logger.debug("No BACKEND_PLUGIN_ENTITY_OVERRIDES configured")
                return

            # Create a simple plugin registry adapter
            class PluginRegistryAdapter:
                def get(self, plugin_id):
                    return plugin_registry.get_plugin(plugin_id)

            override_registry.load_from_settings(override_config, PluginRegistryAdapter())

        except Exception as e:
            logger.error(f"Failed to load override configuration: {e}", exc_info=True)

    def _inject_models(self):
        """Inject real models into the plugin SDK"""
        try:
            # Import real models from AirOne
            # Import plugin SDK models module
            import pagoda_plugin_sdk.models as sdk_models

            from entity.models import Entity, EntityAttr
            from entry.models import Attribute, AttributeValue, Entry
            from job.models import Job
            from user.models import User

            # Inject real models
            sdk_models.Entity = Entity
            sdk_models.Entry = Entry
            sdk_models.User = User
            sdk_models.AttributeValue = AttributeValue
            sdk_models.EntityAttr = EntityAttr
            sdk_models.Attribute = Attribute
            sdk_models.Job = Job

            logger.info("Successfully injected models into plugin SDK")

        except ImportError as e:
            logger.error(f"Failed to inject models into plugin SDK: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during model injection: {e}")
            raise

    def get_installed_apps(self) -> List[str]:
        """Get list of apps to add to Django INSTALLED_APPS

        Returns an empty list if plugins are disabled.

        Returns:
            List of Django application names from enabled plugins
        """
        if not self.is_plugins_enabled():
            return []

        self.initialize()
        return plugin_registry.get_installed_apps()

    def get_url_patterns(self) -> List[Any]:
        """Get URL patterns

        Returns an empty list if plugins are disabled.

        Returns:
            List of URL patterns from enabled plugins
        """
        if not self.is_plugins_enabled():
            return []

        self.initialize()
        return plugin_registry.get_url_patterns()

    def get_api_v2_patterns(self) -> List[Any]:
        """Get API v2 URL patterns

        Returns an empty list if plugins are disabled.

        Returns:
            List of API v2 URL patterns from enabled plugins
        """
        if not self.is_plugins_enabled():
            return []

        self.initialize()
        return plugin_registry.get_api_v2_patterns()

    def get_plugin_count(self) -> int:
        """Get the number of registered plugins

        Returns:
            Total number of plugins
        """
        if not self.is_plugins_enabled():
            return 0

        self.initialize()
        return len(plugin_registry.get_all_plugins())

    def get_enabled_plugin_count(self) -> int:
        """Get the number of enabled plugins

        Returns:
            Number of enabled plugins
        """
        if not self.is_plugins_enabled():
            return 0

        self.initialize()
        return len(plugin_registry.get_enabled_plugins())


# Global instance
plugin_integration = PluginIntegration()
