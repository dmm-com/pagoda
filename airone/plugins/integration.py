import logging
import os
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

        Controlled by the environment variable AIRONE_PLUGINS_ENABLED.
        Default is False (disabled).

        Returns:
            True if plugins are enabled
        """
        return getattr(settings, 'AIRONE_PLUGINS_ENABLED', False)

    def initialize(self):
        """Initialize the plugin system

        Only executes plugin auto-discovery if plugins are enabled.
        """
        if not self.initialized and self.is_plugins_enabled():
            logger.info("Initializing plugin system...")
            discover_plugins()
            self.initialized = True
            logger.info("Plugin system initialized successfully")

    def get_installed_apps(self) -> List[str]:
        """Get list of apps to add to Django INSTALLED_APPS

        Returns an empty list if plugins are disabled.

        Returns:
            List of Django application names from enabled plugins
        """
        if not self.is_plugins_enabled():
            return []

        self.initialize()
        apps = plugin_registry.get_installed_apps()

        # Special handling for sample plugins
        sample_apps = []
        for plugin in plugin_registry.get_enabled_plugins():
            if self._is_sample_plugin(plugin.id):
                # For sample plugins, adjust to proper path
                for app in plugin.django_apps:
                    if app == plugin.id.replace('-', '_'):
                        sample_app = f"plugin_samples.{app}.{app}"
                        sample_apps.append(sample_app)
                        logger.debug(f"Added sample plugin app: {sample_app}")

        # Combine with external plugin apps
        external_apps = [app for app in apps if not self._is_sample_app(app)]

        return external_apps + sample_apps

    def _is_sample_plugin(self, plugin_id: str) -> bool:
        """Determine if a plugin is a sample plugin"""
        # Determination based on sample plugin naming conventions
        sample_plugin_patterns = [
            "hello-world-plugin",
            "entry-analytics-plugin",
        ]
        return any(plugin_id.startswith(pattern) for pattern in sample_plugin_patterns)

    def _is_sample_app(self, app_name: str) -> bool:
        """Determine if an app is a sample plugin app"""
        return app_name.startswith("plugin_samples.")

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

    def get_job_operations(self) -> dict:
        """Get plugin job operations

        Returns an empty dictionary if plugins are disabled.

        Returns:
            Dictionary of plugin job operations
        """
        if not self.is_plugins_enabled():
            return {}

        self.initialize()
        return plugin_registry.get_job_operations()

    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute plugin hooks

        Returns an empty list if plugins are disabled.

        Args:
            hook_name: Hook name
            *args: Positional arguments to pass to hooks
            **kwargs: Keyword arguments to pass to hooks

        Returns:
            List of execution results from each callback
        """
        if not self.is_plugins_enabled():
            return []

        self.initialize()
        return plugin_registry.call_hook(hook_name, *args, **kwargs)

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