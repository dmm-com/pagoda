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
        if not self.id.replace("-", "").replace("_", "").isalnum():
            raise PluginValidationError(
                "Plugin ID must contain only alphanumeric characters, hyphens, and underscores"
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
        }

    def __str__(self) -> str:
        return f"{self.name} v{self.version} ({self.id})"

    def __repr__(self) -> str:
        return f"<Plugin: {self.id}>"
