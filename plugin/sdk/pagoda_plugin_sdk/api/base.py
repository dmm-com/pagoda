"""
Base classes for plugin API views.

These base classes provide common functionality for plugin API endpoints,
including authentication, permission checking, error handling, and
integration with the host application's plugin system.
"""

import logging
from typing import Any, Dict, Optional

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from ..exceptions import PluginError
from ..mixins import PluginAPIViewMixin

logger = logging.getLogger(__name__)


class PluginAPIView(PluginAPIViewMixin):
    """Base API view for plugins

    Extends PluginAPIViewMixin with additional plugin-specific functionality:
    - Plugin context management
    - Standardized error responses
    - Integration with host application services

    Usage:
        class MyPluginView(PluginAPIView):
            plugin_id = "my-plugin"

            def get(self, request):
                context = self.get_plugin_context()
                return Response({"message": f"Hello from {context['plugin_id']}!"})
    """

    plugin_id: Optional[str] = None
    plugin_version: Optional[str] = None

    def get_plugin_id(self) -> str:
        """Get the plugin identifier

        Returns:
            Plugin ID string

        Raises:
            NotImplementedError: If plugin_id is not set
        """
        if not self.plugin_id:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define plugin_id or override get_plugin_id()"
            )
        return self.plugin_id

    def get_plugin_version(self) -> Optional[str]:
        """Get the plugin version

        Returns:
            Plugin version string or None
        """
        return self.plugin_version

    def get_plugin_context(self) -> Dict[str, Any]:
        """Get enhanced plugin execution context

        Returns:
            Dictionary containing plugin context information
        """
        context = super().get_plugin_context()
        context.update(
            {
                "plugin_id": self.get_plugin_id(),
                "plugin_version": self.get_plugin_version(),
                "view_name": self.__class__.__name__,
            }
        )
        return context

    def handle_exception(self, exc: Exception) -> Response:
        """Enhanced plugin-specific exception handling

        Args:
            exc: The exception that occurred

        Returns:
            Appropriate error response
        """
        plugin_id = getattr(self, "plugin_id", None) or "unknown"
        logger.error(f"Plugin API error in {plugin_id}: {exc}")

        # Handle plugin-specific exceptions
        if isinstance(exc, PluginError):
            return Response(
                {
                    "error": "plugin_error",
                    "message": str(exc),
                    "plugin_id": plugin_id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delegate to parent for other exceptions
        return super().handle_exception(exc)


class PluginViewSet(viewsets.ModelViewSet):
    """Base ViewSet for plugin models

    Provides a standardized base for plugin ViewSets with:
    - Plugin context management
    - Automatic permission handling
    - Standardized pagination
    - Error handling integration

    Usage:
        class MyModelViewSet(PluginViewSet):
            plugin_id = "my-plugin"
            queryset = MyModel.objects.all()
            serializer_class = MyModelSerializer

            def create(self, request):
                context = self.get_plugin_context()
                # Custom creation logic
                return super().create(request)
    """

    permission_classes = [IsAuthenticated]
    plugin_id: Optional[str] = None
    plugin_version: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_plugin_configuration()

    def _validate_plugin_configuration(self):
        """Validate plugin configuration

        Ensures required plugin attributes are properly configured.
        """
        if not self.plugin_id:
            logger.warning(
                f"{self.__class__.__name__} should define plugin_id for better integration"
            )

    def get_plugin_id(self) -> str:
        """Get the plugin identifier

        Returns:
            Plugin ID string

        Raises:
            NotImplementedError: If plugin_id is not set
        """
        if not self.plugin_id:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define plugin_id or override get_plugin_id()"
            )
        return self.plugin_id

    def get_plugin_version(self) -> Optional[str]:
        """Get the plugin version

        Returns:
            Plugin version string or None
        """
        return self.plugin_version

    def get_plugin_context(self) -> Dict[str, Any]:
        """Get plugin execution context

        Returns:
            Dictionary containing plugin context information
        """
        return {
            "plugin_id": self.get_plugin_id() if self.plugin_id else "unknown",
            "plugin_version": self.get_plugin_version(),
            "viewset_name": self.__class__.__name__,
            "action": getattr(self, "action", None),
            "user": getattr(self.request, "user", None) if hasattr(self, "request") else None,
        }

    def get_queryset(self):
        """Get filtered queryset for the viewset

        Can be overridden by subclasses to add plugin-specific filtering.

        Returns:
            Filtered queryset
        """
        queryset = super().get_queryset()

        # Add plugin-specific filtering if needed
        # This is a hook for subclasses to customize
        return self.filter_queryset_for_plugin(queryset)

    def filter_queryset_for_plugin(self, queryset):
        """Apply plugin-specific filtering to queryset

        Override this method to add custom filtering logic.

        Args:
            queryset: Base queryset

        Returns:
            Filtered queryset
        """
        return queryset

    def handle_exception(self, exc: Exception) -> Response:
        """Plugin-specific exception handling for ViewSets

        Args:
            exc: The exception that occurred

        Returns:
            Appropriate error response
        """
        plugin_id = getattr(self, "plugin_id", None) or "unknown"
        action = getattr(self, "action", "unknown")
        logger.error(f"Plugin ViewSet error in {plugin_id}.{action}: {exc}")

        # Handle plugin-specific exceptions
        if isinstance(exc, PluginError):
            return Response(
                {
                    "error": "plugin_error",
                    "message": str(exc),
                    "plugin_id": plugin_id,
                    "action": action,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delegate to parent for other exceptions
        return super().handle_exception(exc)

    def initialize_request(self, request: Request, *args, **kwargs) -> Request:
        """Initialize request with plugin context

        Adds plugin context to the request object for use in other components.

        Args:
            request: Incoming request

        Returns:
            Enhanced request object
        """
        request = super().initialize_request(request, *args, **kwargs)

        # Add plugin context to request
        if not hasattr(request, "plugin_context"):
            request.plugin_context = self.get_plugin_context()

        return request

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a new model instance with plugin context

        Args:
            request: Request object

        Returns:
            Response with created instance
        """
        logger.info(f"Plugin {self.get_plugin_id()} creating new instance")
        return super().create(request, *args, **kwargs)

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update a model instance with plugin context

        Args:
            request: Request object

        Returns:
            Response with updated instance
        """
        logger.info(f"Plugin {self.get_plugin_id()} updating instance")
        return super().update(request, *args, **kwargs)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete a model instance with plugin context

        Args:
            request: Request object

        Returns:
            Response confirming deletion
        """
        logger.info(f"Plugin {self.get_plugin_id()} deleting instance")
        return super().destroy(request, *args, **kwargs)
