"""
Hello World Plugin for Pagoda

Demonstrates how to create external plugins using the Pagoda plugin system.
"""

import logging

# Import from Pagoda Plugin SDK libraries (fully independent)
from pagoda_plugin_sdk import Plugin

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
    description = "A sample plugin demonstrating Pagoda plugin system capabilities"
    author = "Pagoda Development Team"

    # Django app configuration
    django_apps = ["pagoda_hello_world_plugin"]

    # API v2 endpoint configuration
    api_v2_patterns = "pagoda_hello_world_plugin.api_v2.urls"

    # Hook configurations (dictionary format for plugin registry)
    hooks = {
        "entry.after_create": "pagoda_hello_world_plugin.hooks.after_entry_create",
        "entry.before_update": "pagoda_hello_world_plugin.hooks.before_entry_update",
    }

    def __init__(self):
        """Initialize the Hello World plugin"""
        super().__init__()
        logger.info(f"Initialized {self.name} v{self.version}")
