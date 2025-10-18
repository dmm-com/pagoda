"""
Django application configuration for Hello World Plugin

Configures the plugin as a Django application.
"""

from django.apps import AppConfig


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
        import logging

        logger = logging.getLogger(__name__)

        logger.info("Hello World Plugin (External) is ready!")
