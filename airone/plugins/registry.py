import importlib
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type

from django.urls import URLResolver, include, path
from pagoda_plugin_sdk.exceptions import PluginError

from .hook_manager import hook_manager

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

    def __init__(self) -> None:
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

        # Register API v2 patterns
        self._register_api_v2_patterns(plugin)

        # Register plugin hooks
        self._register_hooks(plugin)

        return plugin

    def _register_api_v2_patterns(self, plugin: Plugin) -> None:
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

    def _register_hooks(self, plugin: Plugin) -> None:
        """Register plugin hook handlers

        Args:
            plugin: Plugin instance whose hooks should be registered
        """
        # Check if plugin has decorator-based hooks
        if not hasattr(plugin.__class__, "_hook_handlers"):
            return

        hook_handlers = plugin.__class__._hook_handlers
        if not hook_handlers:
            return

        registered_count = 0
        for handler_info in hook_handlers:
            try:
                hook_name = handler_info["hook_name"]
                entity = handler_info.get("entity")
                priority = handler_info.get("priority", 100)
                method_name = handler_info["method_name"]

                # Get the bound method from the plugin instance
                handler = getattr(plugin, method_name)

                # Register with entity filtering and priority
                hook_manager.register_hook(
                    hook_name, handler, plugin.id, priority=priority, entity=entity
                )
                registered_count += 1
                logger.debug(
                    f"Registered hook '{hook_name}' (method: {method_name}) "
                    f"for plugin '{plugin.id}'"
                )
            except Exception as e:
                logger.error(
                    f"Failed to register hook '{hook_name}' for plugin '{plugin.id}': {e}",
                    exc_info=True,
                )

        if registered_count > 0:
            logger.info(f"Registered {registered_count} hook(s) for plugin '{plugin.id}'")

    def _load_handler(self, handler_path: str) -> Callable:
        """Load handler function from module path

        Args:
            handler_path: Module path in format 'module.path.function_name'

        Returns:
            Callable handler function

        Raises:
            ImportError: If module cannot be imported
            AttributeError: If function doesn't exist in module
        """
        # Split into module path and function name
        try:
            module_path, func_name = handler_path.rsplit(".", 1)
        except ValueError:
            raise ImportError(
                f"Invalid handler path '{handler_path}'. "
                f"Expected format: 'module.path.function_name'"
            )

        # Import the module
        module = importlib.import_module(module_path)

        # Get the function from the module
        if not hasattr(module, func_name):
            raise AttributeError(f"Function '{func_name}' not found in module '{module_path}'")

        return getattr(module, func_name)

    def get(self, plugin_id: str) -> Optional["Plugin"]:
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

    def get_url_patterns(self) -> List[URLResolver]:
        """Get URL patterns

        Returns:
            List of URL patterns from enabled plugins
        """
        patterns: List[URLResolver] = []
        for plugin in self.get_enabled_plugins():
            if plugin.url_patterns:
                patterns.append(path(f"plugins/{plugin.id}/", include(plugin.url_patterns)))
        return patterns

    def get_api_v2_patterns(self) -> List[URLResolver]:
        """Get API v2 URL patterns

        Returns:
            List of API v2 URL patterns from enabled plugins
        """
        patterns: List[URLResolver] = []
        for pattern_config in self._api_v2_patterns:
            patterns.append(path(pattern_config["prefix"], include(pattern_config["patterns"])))
        return patterns


# Global registry instance
plugin_registry = PluginRegistry()
