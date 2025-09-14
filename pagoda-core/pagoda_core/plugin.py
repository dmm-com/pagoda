"""
Base Plugin class for the Pagoda plugin system.

All plugins must inherit from the Plugin class defined here.
This provides the foundation for plugin discovery, validation, and lifecycle management.
"""

from typing import Any, Dict, List, Optional
from .exceptions import PluginValidationError


class Plugin:
    """Base class for all Pagoda plugins

    All plugins must inherit from this class and define the required attributes.
    This class is designed to be completely independent from any host application.
    """

    # Required attributes - must be defined by subclasses
    id: str = ""
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""

    # Optional attributes
    dependencies: List[str] = []

    # Django integration
    django_apps: List[str] = []
    url_patterns: Optional[str] = None
    api_v2_patterns: Optional[str] = None

    # Job operations (operation_id: config)
    job_operations: Dict[int, Dict[str, Any]] = {}

    # Hooks (hook_name: handler_path)
    hooks: Dict[str, str] = {}

    def __init__(self):
        """Initialize the plugin instance"""
        self.validate()

    def validate(self):
        """Validate plugin configuration

        Raises:
            PluginValidationError: If validation fails
        """
        if not self.id:
            raise PluginValidationError("Plugin ID is required")

        if not self.name:
            raise PluginValidationError("Plugin name is required")

        if not self.version:
            raise PluginValidationError("Plugin version is required")

        # Validate ID format (alphanumeric, hyphens, underscores only)
        if not self.id.replace('-', '').replace('_', '').isalnum():
            raise PluginValidationError(
                "Plugin ID must contain only alphanumeric characters, hyphens, and underscores"
            )

        # Validate job operation IDs are in valid range (1000-9999)
        for op_id in self.job_operations.keys():
            if not isinstance(op_id, int) or not (1000 <= op_id <= 9999):
                raise PluginValidationError(
                    f"Job operation ID {op_id} must be an integer between 1000 and 9999"
                )

        # Validate django_apps contains valid app names
        for app in self.django_apps:
            if not app or not isinstance(app, str):
                raise PluginValidationError("Django app names must be non-empty strings")

    def get_info(self) -> Dict[str, Any]:
        """Get plugin metadata

        Returns:
            Dictionary containing plugin information
        """
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "django_apps": self.django_apps,
            "url_patterns": self.url_patterns,
            "api_v2_patterns": self.api_v2_patterns,
            "hooks": list(self.hooks.keys()),
            "job_operations": list(self.job_operations.keys()),
        }

    def is_enabled(self) -> bool:
        """Check if plugin is enabled

        Returns:
            True if plugin is enabled, False otherwise

        Note:
            Default implementation always returns True.
            Subclasses can override this method for custom enable/disable logic.
        """
        return True

    def activate(self):
        """Called when plugin is activated

        Override this method to perform plugin-specific activation logic.
        This is called after the plugin is loaded and registered.
        """
        pass

    def deactivate(self):
        """Called when plugin is deactivated

        Override this method to perform plugin-specific cleanup logic.
        This is called before the plugin is unloaded.
        """
        pass

    def get_installed_apps(self) -> List[str]:
        """Get Django apps that should be installed

        Returns:
            List of Django app names

        Note:
            This method returns the django_apps attribute by default.
            Subclasses can override for dynamic app determination.
        """
        return self.django_apps[:]

    def get_url_patterns(self):
        """Get URL patterns for this plugin

        Returns:
            URL patterns or None if not applicable

        Note:
            Host applications are responsible for importing and including
            the patterns specified in url_patterns attribute.
        """
        if not self.url_patterns:
            return None

        # Return the import path - host application handles actual import
        return self.url_patterns

    def get_api_v2_patterns(self):
        """Get API v2 URL patterns for this plugin

        Returns:
            API v2 URL patterns or None if not applicable

        Note:
            Host applications are responsible for importing and including
            the patterns specified in api_v2_patterns attribute.
        """
        if not self.api_v2_patterns:
            return None

        # Return the import path - host application handles actual import
        return self.api_v2_patterns

    def __str__(self) -> str:
        return f"{self.name} v{self.version} ({self.id})"

    def __repr__(self) -> str:
        return f"<Plugin: {self.id}>"