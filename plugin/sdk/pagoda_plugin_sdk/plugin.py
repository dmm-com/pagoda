"""
Base Plugin class for the Pagoda plugin system.

All plugins must inherit from the Plugin class defined here.
This provides the foundation for plugin discovery, validation, and lifecycle management.
"""

from typing import Any, Callable, ClassVar, Dict, List, Optional, Type

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

    # Plugin-specific parameter model for override configuration
    # Subclasses can set this to a Pydantic BaseModel class for validation
    params_model: ClassVar[Optional[Type[Any]]] = None

    # Hook handlers - populated by __init_subclass__
    _hook_handlers: ClassVar[List[Dict[str, Any]]] = []

    def __init_subclass__(cls, **kwargs):
        """Automatically detect and register decorated hook methods"""
        super().__init_subclass__(**kwargs)

        # Scan for decorated methods
        cls._hook_handlers = []
        for attr_name in dir(cls):
            # Skip private/magic methods
            if attr_name.startswith("_"):
                continue

            attr = getattr(cls, attr_name)
            # Check if method has hook metadata from decorator
            if callable(attr) and hasattr(attr, "_hook_metadata"):
                metadata = attr._hook_metadata
                cls._hook_handlers.append(
                    {
                        "hook_name": metadata["hook_name"],
                        "entity": metadata.get("entity"),
                        "priority": metadata.get("priority", 100),
                        "method_name": attr_name,
                        "handler": attr,
                    }
                )

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

    def validate_params(self, params: Dict[str, Any]) -> Any:
        """Validate plugin parameters using the params_model if defined.

        If params_model is defined (a Pydantic BaseModel), the params will
        be validated and returned as a model instance. Otherwise, the raw
        dict is returned.

        Args:
            params: Raw parameter dictionary from configuration

        Returns:
            Validated params (Pydantic model instance or dict)

        Raises:
            ValidationError: If params don't match the model schema
        """
        if self.params_model is None:
            return params

        # Assumes params_model is a Pydantic BaseModel
        return self.params_model(**params)

    def get_handler(self, operation: str) -> Optional[Callable]:
        """Get the override handler for a specific operation.

        This method scans the plugin instance for methods decorated with
        @override_operation and returns the handler for the specified operation.

        Args:
            operation: Operation type string ("create", "retrieve", etc.)

        Returns:
            Handler callable if found, None otherwise
        """
        # Import here to avoid circular imports
        try:
            from .override import OVERRIDE_META_ATTR
        except ImportError:
            return None

        operation_lower = operation.lower()

        for attr_name in dir(self):
            if attr_name.startswith("_"):
                continue

            try:
                attr = getattr(self, attr_name)
            except AttributeError:
                continue

            if not callable(attr):
                continue

            meta = getattr(attr, OVERRIDE_META_ATTR, None)
            if meta and meta.operation == operation_lower:
                return attr

        return None

    def get_info(self) -> Dict[str, Any]:
        """Get plugin metadata

        Returns:
            Dictionary containing plugin information
        """
        # Extract unique hook names from registered handlers
        hook_names = set()
        if hasattr(self.__class__, "_hook_handlers"):
            for handler_info in self.__class__._hook_handlers:
                hook_names.add(handler_info["hook_name"])

        # Collect override operations
        override_operations = []
        try:
            from .override import OVERRIDE_META_ATTR

            for attr_name in dir(self):
                if attr_name.startswith("_"):
                    continue
                try:
                    attr = getattr(self, attr_name)
                except AttributeError:
                    continue
                if callable(attr):
                    meta = getattr(attr, OVERRIDE_META_ATTR, None)
                    if meta:
                        override_operations.append(meta.operation)
        except ImportError:
            pass

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
            "hooks": list(hook_names),
            "override_operations": override_operations,
            "has_params_model": self.params_model is not None,
        }

    def __str__(self) -> str:
        return f"{self.name} v{self.version} ({self.id})"

    def __repr__(self) -> str:
        return f"<Plugin: {self.id}>"
