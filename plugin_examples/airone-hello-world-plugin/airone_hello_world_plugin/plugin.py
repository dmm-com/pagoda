"""
Hello World Plugin for AirOne

Demonstrates how to create external plugins using the AirOne plugin system.
"""

import logging
from typing import List, Any

# Import from Pagoda Core libraries (fully independent)
from pagoda_core import Plugin

logger = logging.getLogger(__name__)


class HelloWorldPlugin(Plugin):
    """Hello World Plugin

    A sample plugin that demonstrates:
    - Basic plugin structure
    - API endpoint registration
    - Hook system integration
    - Core functionality access
    """

    # Plugin metadata
    id = "hello-world-plugin"
    name = "Hello World Plugin"
    version = "1.0.0"
    description = "A sample plugin demonstrating AirOne plugin system capabilities"
    author = "AirOne Development Team"

    # Django app configuration
    django_apps = ["airone_hello_world_plugin"]

    # API v2 endpoint configuration
    api_v2_patterns = "airone_hello_world_plugin.api_v2.urls"

    # Job operations (empty for this sample plugin)
    job_operations = {}

    # Hook configurations (dictionary format for plugin registry)
    hooks = {
        "entry.after_create": "airone_hello_world_plugin.hooks.after_entry_create",
        "entry.before_update": "airone_hello_world_plugin.hooks.before_entry_update",
    }

    def __init__(self):
        """Initialize the Hello World plugin"""
        super().__init__()
        logger.info(f"Initialized {self.name} v{self.version}")

    def get_installed_apps(self) -> List[str]:
        """Return Django apps to be installed

        Returns:
            List of Django app names
        """
        return [self.django_app_name]

    def get_api_v2_patterns(self) -> Any:
        """Return API v2 URL patterns

        Returns:
            URL patterns for API v2 endpoints
        """
        try:
            from django.urls import include, path
            return [
                path("plugins/hello-world-plugin/", include(self.api_v2_patterns))
            ]
        except ImportError:
            logger.error("Failed to import Django URL utilities")
            return []

    def activate(self):
        """Activate the plugin

        Called when the plugin is activated/loaded.
        """
        logger.info(f"Activating {self.name}")

        # Plugin-specific activation logic
        self._register_hooks()
        self._initialize_resources()

    def deactivate(self):
        """Deactivate the plugin

        Called when the plugin is deactivated/unloaded.
        """
        logger.info(f"Deactivating {self.name}")

        # Plugin-specific deactivation logic
        self._cleanup_resources()

    def _register_hooks(self):
        """Register plugin hooks"""
        for hook in self.hooks:
            logger.info(f"Registering hook: {hook['name']}")

    def _initialize_resources(self):
        """Initialize plugin resources"""
        logger.info("Initializing Hello World plugin resources")

    def _cleanup_resources(self):
        """Cleanup plugin resources"""
        logger.info("Cleaning up Hello World plugin resources")