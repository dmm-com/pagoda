"""
AirOne Bridge Manager

Manages the connection between pagoda-core interfaces and AirOne implementations.
Provides a single access point for plugins to interact with AirOne through
standardized interfaces.
"""

import logging
from typing import Any, Dict, Optional

from .bridge import AirOneAuthBridge, AirOneDataBridge, AirOneHookBridge

logger = logging.getLogger(__name__)


class AirOneBridgeManager:
    """Manages bridges between pagoda-core and AirOne

    This class provides a centralized way to access AirOne-specific implementations
    of pagoda-core interfaces. It acts as a service locator for plugins to access
    AirOne functionality through standardized interfaces.
    """

    def __init__(self):
        self._auth_bridge: Optional[AirOneAuthBridge] = None
        self._data_bridge: Optional[AirOneDataBridge] = None
        self._hook_bridge: Optional[AirOneHookBridge] = None
        self._initialized = False

    def initialize(self):
        """Initialize all bridge implementations"""
        if self._initialized:
            return

        try:
            self._auth_bridge = AirOneAuthBridge()
            self._data_bridge = AirOneDataBridge()
            self._hook_bridge = AirOneHookBridge()

            # Register Django signals for hook integration
            self._hook_bridge.register_django_signals()

            self._initialized = True
            logger.info("AirOne bridge manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize AirOne bridge manager: {e}")
            raise

    @property
    def auth(self) -> AirOneAuthBridge:
        """Get the authentication bridge

        Returns:
            AirOneAuthBridge instance for authentication operations
        """
        if not self._initialized:
            self.initialize()
        return self._auth_bridge

    @property
    def data(self) -> AirOneDataBridge:
        """Get the data access bridge

        Returns:
            AirOneDataBridge instance for data operations
        """
        if not self._initialized:
            self.initialize()
        return self._data_bridge

    @property
    def hooks(self) -> AirOneHookBridge:
        """Get the hook system bridge

        Returns:
            AirOneHookBridge instance for hook operations
        """
        if not self._initialized:
            self.initialize()
        return self._hook_bridge

    def get_service_info(self) -> Dict[str, Any]:
        """Get information about available services

        Returns:
            Dictionary containing service information
        """
        if not self._initialized:
            self.initialize()

        return {
            "auth_bridge": {
                "class": self._auth_bridge.__class__.__name__,
                "available": self._auth_bridge is not None,
            },
            "data_bridge": {
                "class": self._data_bridge.__class__.__name__,
                "available": self._data_bridge is not None,
            },
            "hook_bridge": {
                "class": self._hook_bridge.__class__.__name__,
                "available": self._hook_bridge is not None,
                "available_hooks": len(self._hook_bridge.get_available_hooks()) if self._hook_bridge else 0,
                "registered_hooks": len(self._hook_bridge._hooks) if self._hook_bridge else 0,
            },
            "initialized": self._initialized,
        }

    def register_plugin_hooks(self, plugin):
        """Register hooks for a plugin

        Args:
            plugin: Plugin instance with hooks to register
        """
        if not self._initialized:
            self.initialize()

        if not hasattr(plugin, 'hooks') or not plugin.hooks:
            return

        hooks_registered = 0
        for hook_name, handler_path in plugin.hooks.items():
            try:
                # Dynamically import and register the handler
                module_path, func_name = handler_path.rsplit(".", 1)
                from importlib import import_module

                module = import_module(module_path)
                handler = getattr(module, func_name)

                if self._hook_bridge.register_hook(hook_name, handler):
                    hooks_registered += 1
                    logger.debug(f"Registered hook {hook_name} for plugin {plugin.id}")
                else:
                    logger.warning(f"Failed to register hook {hook_name} for plugin {plugin.id}")

            except Exception as e:
                logger.error(f"Error registering hook {hook_name} for plugin {plugin.id}: {e}")

        if hooks_registered > 0:
            logger.info(f"Registered {hooks_registered} hooks for plugin {plugin.id}")

    def unregister_plugin_hooks(self, plugin):
        """Unregister hooks for a plugin

        Args:
            plugin: Plugin instance with hooks to unregister
        """
        if not self._initialized or not hasattr(plugin, 'hooks') or not plugin.hooks:
            return

        hooks_unregistered = 0
        for hook_name, handler_path in plugin.hooks.items():
            try:
                # Dynamically import and unregister the handler
                module_path, func_name = handler_path.rsplit(".", 1)
                from importlib import import_module

                module = import_module(module_path)
                handler = getattr(module, func_name)

                if self._hook_bridge.unregister_hook(hook_name, handler):
                    hooks_unregistered += 1
                    logger.debug(f"Unregistered hook {hook_name} for plugin {plugin.id}")

            except Exception as e:
                logger.error(f"Error unregistering hook {hook_name} for plugin {plugin.id}: {e}")

        if hooks_unregistered > 0:
            logger.info(f"Unregistered {hooks_unregistered} hooks for plugin {plugin.id}")


# Global bridge manager instance
bridge_manager = AirOneBridgeManager()


def get_auth_bridge():
    """Get the global authentication bridge"""
    return bridge_manager.auth


def get_data_bridge():
    """Get the global data access bridge"""
    return bridge_manager.data


def get_hook_bridge():
    """Get the global hook system bridge"""
    return bridge_manager.hooks