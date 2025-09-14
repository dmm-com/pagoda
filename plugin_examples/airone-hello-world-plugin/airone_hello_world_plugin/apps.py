"""
Django application configuration for Hello World Plugin

Configures the plugin as a Django application.
"""

from django.apps import AppConfig


class HelloWorldPluginConfig(AppConfig):
    """Django application configuration for Hello World Plugin"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'airone_hello_world_plugin'
    label = 'airone_hello_world_plugin'
    verbose_name = 'AirOne Hello World Plugin (External)'

    def ready(self):
        """Initialize the plugin when Django is ready

        This method is called when Django has finished loading all applications.
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info("Hello World Plugin (External) is ready!")

        # Register signal handlers if needed
        try:
            self._register_signal_handlers()
        except Exception as e:
            logger.error(f"Failed to register signal handlers: {e}")

    def _register_signal_handlers(self):
        """Register Django signal handlers

        Connects the plugin's hook functions to Django signals.
        """
        import logging
        from django.db.models.signals import post_save, pre_save

        logger = logging.getLogger(__name__)

        try:
            # Import hook functions
            from .hooks import after_entry_create, before_entry_update

            # Register hooks for Entry model (when available)
            try:
                from entry.models import Entry
                post_save.connect(after_entry_create, sender=Entry)
                pre_save.connect(before_entry_update, sender=Entry)
                logger.info("Registered signal handlers for Entry model")
            except ImportError:
                logger.info("Entry model not available, skipping Entry signal handlers")

        except ImportError as e:
            logger.warning(f"Could not import hook functions: {e}")
        except Exception as e:
            logger.error(f"Error registering signal handlers: {e}")