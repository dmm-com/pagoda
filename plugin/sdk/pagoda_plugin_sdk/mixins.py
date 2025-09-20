"""
Mixin classes for plugin development.

These mixins provide common functionality that plugins can inherit to integrate
with the host application's systems like authentication, job processing, etc.
"""

import logging
from typing import Any, Dict

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class PluginAPIViewMixin(APIView):
    """Base mixin for plugin API views

    This mixin provides:
    - Default authentication requirements
    - Plugin context validation
    - Standardized error handling
    - Integration hooks for host applications

    Usage:
        class MyPluginView(PluginAPIViewMixin):
            def get(self, request):
                return Response({"message": "Hello from my plugin!"})
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_plugin_context()

    def _validate_plugin_context(self):
        """Validate plugin execution context

        This method can be overridden by subclasses or host applications
        to perform plugin-specific validation.
        """
        # Basic validation - can be extended by host applications
        pass

    def handle_exception(self, exc: Exception) -> Any:
        """Plugin-specific exception handling

        Provides centralized error handling for plugin API views.

        Args:
            exc: The exception that occurred

        Returns:
            The appropriate error response
        """
        plugin_class = self.__class__.__name__
        logger.error(f"Plugin API error in {plugin_class}: {exc}")
        return super().handle_exception(exc)

    def get_plugin_context(self) -> Dict[str, Any]:
        """Get plugin execution context

        Returns context information that might be useful for the plugin.
        Host applications can override this to provide additional context.

        Returns:
            Dictionary containing context information
        """
        return {
            "plugin_view": self.__class__.__name__,
            "user": getattr(self.request, "user", None) if hasattr(self, "request") else None,
        }


class PluginJobMixin:
    """Base mixin for plugin background jobs

    This mixin provides utilities for Celery tasks and background jobs:
    - Progress tracking
    - Error handling
    - Logging integration
    - Job lifecycle management

    Usage:
        from celery import shared_task
        from pagoda_core import PluginJobMixin

        @shared_task(bind=True)
        class MyPluginJob(PluginJobMixin):
            def run(self, *args, **kwargs):
                self.update_progress(50, "Processing data...")
                # Do work here
                self.update_progress(100, "Complete!")
    """

    def update_progress(self, progress: int, message: str = ""):
        """Update job progress

        Args:
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        if not (0 <= progress <= 100):
            logger.warning(f"Invalid progress value: {progress}. Should be 0-100.")
            return

        logger.info(f"Plugin job progress: {progress}% - {message}")

        # Host applications can override this method to update
        # actual job status in their job management system

    def handle_error(self, error: Exception):
        """Handle job errors

        Provides centralized error handling for plugin jobs.

        Args:
            error: The error that occurred
        """
        job_class = self.__class__.__name__
        logger.error(f"Plugin job error in {job_class}: {error}")

        # Host applications can override this method to integrate
        # with their error handling and notification systems

    def log_info(self, message: str):
        """Log informational message

        Args:
            message: Message to log
        """
        logger.info(f"Plugin job: {message}")

    def log_warning(self, message: str):
        """Log warning message

        Args:
            message: Warning message to log
        """
        logger.warning(f"Plugin job warning: {message}")

    def log_error(self, message: str):
        """Log error message

        Args:
            message: Error message to log
        """
        logger.error(f"Plugin job error: {message}")

    def get_job_context(self):
        """Get job execution context

        Returns context information that might be useful for the job.
        Host applications can override this to provide additional context.

        Returns:
            Dictionary containing context information
        """
        return {
            "job_class": self.__class__.__name__,
        }
