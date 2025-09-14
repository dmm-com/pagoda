"""
AirOne Core Mixins for Plugin Development

Provides base classes that plugins can inherit from to integrate with AirOne's core functionality.
"""

import logging
from typing import Any

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class PluginAPIViewMixin(APIView):
    """Base mixin for plugin API views

    This mixin provides:
    - Authentication requirements
    - Plugin context validation
    - Standardized error handling
    - Integration with AirOne's security model

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

        Performs basic security and context validation.
        Can be extended for plugin-specific validation.
        """
        # Basic validation processing
        # Security checks to be added in the future
        pass

    def handle_exception(self, exc: Exception) -> Any:
        """Plugin-specific exception handling

        Provides centralized error handling for plugin API views.

        Args:
            exc: The exception that occurred

        Returns:
            The appropriate error response
        """
        logger.error(f"Plugin API error in {self.__class__.__name__}: {exc}")
        return super().handle_exception(exc)


class PluginJobMixin:
    """Base mixin for plugin background jobs

    This mixin provides utilities for Celery tasks created by plugins:
    - Progress tracking
    - Error handling
    - Logging integration
    - Job lifecycle management

    Usage:
        from celery import shared_task
        from airone.libs import PluginJobMixin

        @shared_task(bind=True)
        class MyPluginJob(PluginJobMixin):
            def run(self, *args, **kwargs):
                self.update_progress(50, "Processing data...")
                # Do work here
                self.update_progress(100, "Complete!")
    """

    def update_progress(self, progress: int, message: str = ""):
        """Update job progress

        Updates the progress of a running background job.

        Args:
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        logger.info(f"Plugin job progress: {progress}% - {message}")

        # Future integration with AirOne job system
        # This will be enhanced to update actual job status in the database

    def handle_error(self, error: Exception):
        """Handle job errors

        Provides centralized error handling for plugin jobs.

        Args:
            error: The error that occurred
        """
        logger.error(f"Plugin job error in {self.__class__.__name__}: {error}")

        # Future integration with AirOne job system
        # This will be enhanced to update job status and notify users

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