"""
Django application configuration for Hello World Plugin

Configures the plugin as a Django application.
"""

import logging

from django.apps import AppConfig

from .config import PLUGIN_TASK_CONFIG
from airone.lib.plugin_task import PluginTaskRegistry


class HelloWorldPluginConfig(AppConfig):
    """Django application configuration for Hello World Plugin"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "pagoda_hello_world_plugin"
    label = "pagoda_hello_world_plugin"
    verbose_name = "Pagoda Hello World Plugin (External)"

    def ready(self):
        """Initialize the plugin when Django is ready

        This method is called when Django has finished loading all applications.
        """
        logger = logging.getLogger(__name__)

        try:
            PluginTaskRegistry.register(PLUGIN_TASK_CONFIG)
            logger.info("Hello World Plugin registered with PluginTaskRegistry")
        except Exception as e:
            logger.warning(f"Failed to register plugin tasks: {e}")

        logger.info("Hello World Plugin (External) is ready!")
