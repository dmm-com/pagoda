"""
AirOne Plugin Base Classes and Exceptions

Provides the foundation classes and exceptions that all plugins must use.
These are exported to external plugins through airone.libs.
"""

from typing import Any, Dict, List, Optional


class PluginError(Exception):
    """Base exception for plugin-related errors"""
    pass


class PluginLoadError(PluginError):
    """Exception raised when plugin loading fails"""
    pass


class PluginValidationError(PluginError):
    """Exception raised when plugin validation fails"""
    pass


class PluginSecurityError(PluginError):
    """Exception raised when plugin security is violated"""
    pass


class Plugin:
    """Base class for all plugins

    All plugins must inherit from this class and define the required attributes.
    This class is available to external plugins through airone.libs.
    """

    # Required attributes
    id: str = ""
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""

    # Dependencies
    dependencies: List[str] = []

    # Django configuration
    django_apps: List[str] = []
    url_patterns: Optional[str] = None
    api_v2_patterns: Optional[str] = None

    # Job operations
    job_operations: Dict[int, Dict[str, Any]] = {}

    # Hooks
    hooks: Dict[str, str] = {}

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

        # Validate ID format
        if not self.id.replace('-', '').replace('_', '').isalnum():
            raise PluginValidationError("Plugin ID must contain only alphanumeric characters, hyphens, and underscores")

        # Validate job operation IDs are in valid range (1000-9999)
        for op_id in self.job_operations.keys():
            if not (1000 <= op_id <= 9999):
                raise PluginValidationError(
                    f"Job operation ID {op_id} must be between 1000 and 9999"
                )

    def get_info(self) -> Dict[str, Any]:
        """Get plugin information

        Returns:
            Dictionary containing plugin metadata
        """
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
        }

    def activate(self):
        """Called when plugin is activated

        Override this method to perform activation logic.
        """
        pass

    def deactivate(self):
        """Called when plugin is deactivated

        Override this method to perform cleanup logic.
        """
        pass

    def is_enabled(self) -> bool:
        """Check if plugin is enabled

        Returns:
            True if plugin is enabled, False otherwise
        """
        # Default implementation: plugin is always enabled
        # Individual plugins can override this method for custom enable/disable logic
        return True