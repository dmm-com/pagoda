import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Type

from django.urls import path, include

from ..libs.base import Plugin, PluginError, PluginValidationError

logger = logging.getLogger(__name__)


class HookRegistry:
    """Hook (extension point) management system"""

    def __init__(self):
        self._hooks = defaultdict(list)

    def register(self, hook_name: str, callback: str):
        """Register a hook

        Args:
            hook_name: Hook name (e.g., "entry.after_create")
            callback: Callback function path (e.g., "plugin.hooks.after_create_entry")
        """
        self._hooks[hook_name].append(callback)

    def call(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute hooks

        Args:
            hook_name: Name of the hook to execute
            *args: Positional arguments to pass to the hook
            **kwargs: Keyword arguments to pass to the hook

        Returns:
            List of execution results from each callback
        """
        results = []
        for callback_path in self._hooks[hook_name]:
            try:
                # Dynamically import and execute callback function
                module_path, func_name = callback_path.rsplit(".", 1)
                from importlib import import_module
                module = import_module(module_path)
                callback = getattr(module, func_name)
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Hook {hook_name} failed: {e}")
        return results


class PluginRegistry:
    """Plugin registration and management system"""

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._hooks = HookRegistry()
        self._job_operations: Dict[int, Dict[str, Any]] = {}
        self._api_v2_patterns: List[Dict[str, Any]] = []

    def register(self, plugin_class: Type[Plugin]) -> Plugin:
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

        # Register hooks (legacy system)
        self._register_hooks(plugin)

        # Register hooks with bridge manager (new system)
        try:
            from .bridge_manager import bridge_manager
            bridge_manager.register_plugin_hooks(plugin)
        except ImportError:
            logger.debug("Bridge manager not available for hook registration")

        # Register job operations
        self._register_job_operations(plugin)

        # Register API v2 patterns
        self._register_api_v2_patterns(plugin)

        return plugin

    def _register_hooks(self, plugin: Plugin):
        """Register plugin hooks"""
        for hook_name, callback_path in plugin.hooks.items():
            self._hooks.register(hook_name, callback_path)
            logger.debug(f"Registered hook {hook_name} for plugin {plugin.id}")

    def _register_job_operations(self, plugin: Plugin):
        """Register plugin job operations"""
        for op_id, config in plugin.job_operations.items():
            if op_id in self._job_operations:
                raise PluginError(f"Job operation {op_id} already registered")

            self._job_operations[op_id] = {
                "plugin_id": plugin.id,
                "name": config["name"],
                "task": config["task"],
                "parallelizable": config.get("parallelizable", False),
                "cancelable": config.get("cancelable", True),
                "downloadable": config.get("downloadable", False),
            }
            logger.debug(f"Registered job operation {op_id} for plugin {plugin.id}")

    def _register_api_v2_patterns(self, plugin: Plugin):
        """Register plugin API v2 patterns"""
        if plugin.api_v2_patterns:
            self._api_v2_patterns.append({
                "plugin_id": plugin.id,
                "patterns": plugin.api_v2_patterns,
                "prefix": f"plugins/{plugin.id}/",
            })
            logger.debug(f"Registered API v2 patterns for plugin {plugin.id}")

    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin by ID

        Args:
            plugin_id: Plugin ID

        Returns:
            Plugin instance, or None if not found
        """
        return self._plugins.get(plugin_id)

    def get_all_plugins(self) -> List[Plugin]:
        """Get all plugins

        Returns:
            List of plugin instances
        """
        return list(self._plugins.values())

    def get_enabled_plugins(self) -> List[Plugin]:
        """Get enabled plugins

        Returns:
            List of enabled plugin instances
        """
        return [plugin for plugin in self._plugins.values() if plugin.is_enabled()]

    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin

        Args:
            plugin_id: Plugin ID

        Returns:
            True if successful, False if plugin does not exist
        """
        plugin = self.get_plugin(plugin_id)
        if plugin:
            plugin.enable()
            logger.info(f"Enabled plugin: {plugin_id}")
            return True
        return False

    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin

        Args:
            plugin_id: Plugin ID

        Returns:
            True if successful, False if plugin does not exist
        """
        plugin = self.get_plugin(plugin_id)
        if plugin:
            plugin.disable()
            logger.info(f"Disabled plugin: {plugin_id}")
            return True
        return False

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
                patterns.append(
                    path(f"plugins/{plugin.id}/", include(plugin.url_patterns))
                )
        return patterns

    def get_api_v2_patterns(self) -> List[Any]:
        """Get API v2 URL patterns

        Returns:
            List of API v2 URL patterns from enabled plugins
        """
        patterns = []
        for pattern_config in self._api_v2_patterns:
            plugin = self._plugins[pattern_config["plugin_id"]]
            if plugin.is_enabled():
                patterns.append(
                    path(pattern_config["prefix"], include(pattern_config["patterns"]))
                )
        return patterns

    def get_job_operations(self) -> Dict[int, Dict[str, Any]]:
        """Get registered job operations

        Returns:
            Dictionary of job operations (operation ID -> operation config)
        """
        operations = {}
        for op_id, config in self._job_operations.items():
            plugin = self._plugins.get(config["plugin_id"])
            if plugin and plugin.is_enabled():
                operations[op_id] = config
        return operations

    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute hooks

        Args:
            hook_name: Hook name
            *args: Positional arguments to pass to hooks
            **kwargs: Keyword arguments to pass to hooks

        Returns:
            List of execution results from each callback
        """
        return self._hooks.call(hook_name, *args, **kwargs)


# Global registry instance
plugin_registry = PluginRegistry()