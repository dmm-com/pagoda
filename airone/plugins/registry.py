import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type

from django.urls import include, path
from pagoda_plugin_sdk.exceptions import PluginError

if TYPE_CHECKING:
    from pagoda_plugin_sdk.plugin import Plugin
else:
    # Runtime import to avoid import errors when plugin system is disabled
    try:
        from pagoda_plugin_sdk.plugin import Plugin
    except ImportError:
        Plugin = None

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Plugin registration and management system"""

    def __init__(self):
        self._plugins: Dict[str, "Plugin"] = {}
        self._api_v2_patterns: List[Dict[str, Any]] = []

    def register(self, plugin_class: Type["Plugin"]) -> "Plugin":
        """Register a plugin

        Args:
            plugin_class: Plugin class

        Returns:
            Registered plugin instance

        Raises:
            PluginValidationError: If plugin validation fails
            PluginError: If plugin ID is already registered
        """
        plugin = plugin_class()

        # Validate the plugin
        plugin.validate()

        # Check for duplicates
        if plugin.id in self._plugins:
            raise PluginError(f"Plugin '{plugin.id}' is already registered")

        # Register the plugin
        self._plugins[plugin.id] = plugin
        logger.info(f"Registered plugin: {plugin.id} v{plugin.version}")

        # Register hooks with bridge manager (new system)
        try:
            from .bridge_manager import bridge_manager

            bridge_manager.register_plugin_hooks(plugin)
        except ImportError:
            logger.debug("Bridge manager not available for hook registration")

        # Register API v2 patterns
        self._register_api_v2_patterns(plugin)

        return plugin

    def _register_api_v2_patterns(self, plugin: Plugin):
        """Register plugin API v2 patterns"""
        if plugin.api_v2_patterns:
            self._api_v2_patterns.append(
                {
                    "plugin_id": plugin.id,
                    "patterns": plugin.api_v2_patterns,
                    "prefix": f"plugins/{plugin.id}/",
                }
            )
            logger.debug(f"Registered API v2 patterns for plugin {plugin.id}")

    def get_plugin(self, plugin_id: str) -> Optional["Plugin"]:
        """Get a plugin by ID

        Args:
            plugin_id: Plugin ID

        Returns:
            Plugin instance, or None if not found
        """
        return self._plugins.get(plugin_id)

    def get_all_plugins(self) -> List["Plugin"]:
        """Get all plugins

        Returns:
            List of plugin instances
        """
        return list(self._plugins.values())

    def get_enabled_plugins(self) -> List["Plugin"]:
        """Get enabled plugins

        Returns:
            List of enabled plugin instances
        """
        return list(self._plugins.values())

    def get_installed_apps(self) -> List[str]:
        """Get Django apps to add to INSTALLED_APPS

        Returns:
            List of Django apps from enabled plugins
        """
        apps = []
        for plugin in self.get_enabled_plugins():
            apps.extend(plugin.django_apps)
        return apps

    def get_url_patterns(self) -> List[Any]:
        """Get URL patterns

        Returns:
            List of URL patterns from enabled plugins
        """
        patterns = []
        for plugin in self.get_enabled_plugins():
            if plugin.url_patterns:
                patterns.append(path(f"plugins/{plugin.id}/", include(plugin.url_patterns)))
        return patterns

    def get_api_v2_patterns(self) -> List[Any]:
        """Get API v2 URL patterns

        Returns:
            List of API v2 URL patterns from enabled plugins
        """
        patterns = []
        for pattern_config in self._api_v2_patterns:
            patterns.append(path(pattern_config["prefix"], include(pattern_config["patterns"])))
        return patterns


# Global registry instance
plugin_registry = PluginRegistry()
