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
