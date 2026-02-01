"""
Override decorator and utilities for plugin entry operation overrides.

This module provides the SDK interface for plugins to declare
entry operation overrides using decorators.

Example:
    from pagoda_plugin_sdk import Plugin
    from pagoda_plugin_sdk.override import override_operation

    class MyPlugin(Plugin):
        id = "my-plugin"

        @override_operation("create")
        def handle_create(self, context: OverrideContext):
            # Custom creation logic
            # context.entity, context.data, context.params available
            return Response({"id": entry.id}, status=202)
"""

import warnings
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from rest_framework import status
from rest_framework.response import Response

# Type variable for decorated methods
F = TypeVar("F", bound=Callable[..., Any])

# Attribute name for storing override metadata on decorated methods
OVERRIDE_META_ATTR = "_override_meta"


class OverrideOperation(Enum):
    """Operation types that can be overridden."""

    CREATE = "create"
    RETRIEVE = "retrieve"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


@dataclass
class OverrideMeta:
    """Metadata for an override handler method."""

    operation: str
    entity: Optional[str] = None  # Deprecated - kept for backward compatibility
    priority: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "operation": self.operation,
            "priority": self.priority,
        }
        if self.entity:
            result["entity"] = self.entity
        return result


def override_operation(
    operation: str,
    priority: int = 0,
) -> Callable[[F], F]:
    """Decorator to mark a plugin method as an entry operation override.

    This decorator attaches metadata to the method that will be used
    during plugin registration to set up the override handler.

    Unlike override_entry_operation, this decorator does NOT require
    an entity parameter. Entity binding is done via ENTITY_PLUGIN_OVERRIDES
    configuration.

    Args:
        operation: Operation type to override ("create", "retrieve", "update", "delete", "list")
        priority: Priority for future use (not currently implemented)

    Returns:
        Decorated method with override metadata attached

    Example:
        class MyPlugin(Plugin):
            @override_operation("create")
            def handle_create(self, context: OverrideContext):
                with atomic_operation(context.user) as op:
                    entry = op.create_entry(
                        entity_id=context.entity.id,
                        name=context.data["name"],
                        attrs=context.data.get("attrs", {}),
                    )
                    return accepted_response({"id": entry.id})

    Handler signature:
        - All operations: (self, context: OverrideContext) -> Response

    OverrideContext contains:
        - request: DRF Request
        - user: User instance
        - entity: Entity instance
        - entry: Entry instance (for retrieve/update/delete)
        - data: Request data dict (for create/update)
        - params: Plugin-specific parameters from configuration
    """
    # Validate operation
    valid_operations = [op.value for op in OverrideOperation]
    if operation.lower() not in valid_operations:
        raise ValueError(f"Invalid operation: {operation}. Valid operations: {valid_operations}")

    def decorator(method: F) -> F:
        # Attach metadata to the method
        meta = OverrideMeta(
            operation=operation.lower(),
            priority=priority,
        )
        setattr(method, OVERRIDE_META_ATTR, meta)

        @wraps(method)
        def wrapper(*args, **kwargs):
            return method(*args, **kwargs)

        # Copy the metadata to the wrapper
        setattr(wrapper, OVERRIDE_META_ATTR, meta)

        return wrapper  # type: ignore

    return decorator


def override_entry_operation(
    entity: str,
    operation: str,
    priority: int = 0,
) -> Callable[[F], F]:
    """Decorator to mark a plugin method as an entry operation override.

    .. deprecated::
        Use :func:`override_operation` instead. Entity binding should be
        done via ENTITY_PLUGIN_OVERRIDES configuration.

    This decorator attaches metadata to the method that will be used
    during plugin registration to set up the override handler.

    Args:
        entity: Name of the entity to override (DEPRECATED - use config instead)
        operation: Operation type to override ("create", "retrieve", "update", "delete", "list")
        priority: Priority for future use (not currently implemented)

    Returns:
        Decorated method with override metadata attached
    """
    warnings.warn(
        "override_entry_operation is deprecated. Use override_operation instead. "
        "Entity binding should be done via ENTITY_PLUGIN_OVERRIDES configuration.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Validate operation
    valid_operations = [op.value for op in OverrideOperation]
    if operation.lower() not in valid_operations:
        raise ValueError(f"Invalid operation: {operation}. Valid operations: {valid_operations}")

    def decorator(method: F) -> F:
        # Attach metadata to the method
        meta = OverrideMeta(
            entity=entity,
            operation=operation.lower(),
            priority=priority,
        )
        setattr(method, OVERRIDE_META_ATTR, meta)

        @wraps(method)
        def wrapper(*args, **kwargs):
            return method(*args, **kwargs)

        # Copy the metadata to the wrapper
        setattr(wrapper, OVERRIDE_META_ATTR, meta)

        return wrapper  # type: ignore

    return decorator


def get_override_meta(method: Callable) -> Optional[OverrideMeta]:
    """Get override metadata from a decorated method.

    Args:
        method: The method to check

    Returns:
        OverrideMeta if the method is decorated, None otherwise
    """
    return getattr(method, OVERRIDE_META_ATTR, None)


def has_override_meta(method: Callable) -> bool:
    """Check if a method has override metadata.

    Args:
        method: The method to check

    Returns:
        True if the method is decorated with @override_operation or @override_entry_operation
    """
    return hasattr(method, OVERRIDE_META_ATTR)


def collect_override_handlers(plugin_instance: Any) -> List[Dict[str, Any]]:
    """Collect all override handlers from a plugin instance.

    Args:
        plugin_instance: The plugin instance to scan

    Returns:
        List of handler info dictionaries:
        [
            {
                "entity": "Service",  # Optional, may be None for new-style handlers
                "operation": "create",
                "handler": <bound method>,
                "priority": 0,
            },
            ...
        ]
    """
    handlers = []

    for attr_name in dir(plugin_instance):
        if attr_name.startswith("_"):
            continue

        try:
            attr = getattr(plugin_instance, attr_name)
        except AttributeError:
            continue

        if not callable(attr):
            continue

        meta = get_override_meta(attr)
        if meta is not None:
            handlers.append(
                {
                    "entity": meta.entity,  # May be None for new-style handlers
                    "operation": meta.operation,
                    "handler": attr,
                    "priority": meta.priority,
                }
            )

    return handlers


# Response helper functions for override handlers


def success_response(
    data: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK,
) -> Response:
    """Create a success response.

    Args:
        data: Response data (optional)
        status_code: HTTP status code (default: 200)

    Returns:
        DRF Response object
    """
    return Response(data or {}, status=status_code)


def created_response(
    data: Optional[Dict[str, Any]] = None,
    entry_id: Optional[int] = None,
    entry_name: Optional[str] = None,
) -> Response:
    """Create a 201 Created response.

    Args:
        data: Response data (optional, overrides entry_id/entry_name if provided)
        entry_id: ID of the created entry
        entry_name: Name of the created entry

    Returns:
        DRF Response object with 201 status
    """
    if data is None:
        data = {}
        if entry_id is not None:
            data["id"] = entry_id
        if entry_name is not None:
            data["name"] = entry_name

    return Response(data, status=status.HTTP_201_CREATED)


def accepted_response(
    data: Optional[Dict[str, Any]] = None,
    message: str = "Request accepted for processing",
) -> Response:
    """Create a 202 Accepted response (for async operations).

    Args:
        data: Response data (optional)
        message: Message to include

    Returns:
        DRF Response object with 202 status
    """
    response_data = data or {}
    if "message" not in response_data:
        response_data["message"] = message

    return Response(response_data, status=status.HTTP_202_ACCEPTED)


def no_content_response() -> Response:
    """Create a 204 No Content response (for delete operations).

    Returns:
        DRF Response object with 204 status
    """
    return Response(status=status.HTTP_204_NO_CONTENT)


def error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Dict[str, Any]] = None,
) -> Response:
    """Create an error response.

    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        details: Additional error details

    Returns:
        DRF Response object
    """
    data = {"error": message}
    if details:
        data["details"] = details

    return Response(data, status=status_code)


def not_found_response(
    message: str = "Entry not found",
) -> Response:
    """Create a 404 Not Found response.

    Args:
        message: Error message

    Returns:
        DRF Response object with 404 status
    """
    return Response({"error": message}, status=status.HTTP_404_NOT_FOUND)


def permission_denied_response(
    message: str = "Permission denied",
    denied_entries: Optional[List[int]] = None,
) -> Response:
    """Create a 403 Forbidden response.

    Args:
        message: Error message
        denied_entries: List of entry IDs that were denied

    Returns:
        DRF Response object with 403 status
    """
    data: Dict[str, Any] = {"error": message}
    if denied_entries:
        data["denied_entries"] = denied_entries

    return Response(data, status=status.HTTP_403_FORBIDDEN)


def validation_error_response(
    errors: Union[Dict[str, Any], List[str], str],
) -> Response:
    """Create a validation error response.

    Args:
        errors: Validation errors (dict, list, or string)

    Returns:
        DRF Response object with 400 status
    """
    if isinstance(errors, str):
        errors = {"detail": errors}

    return Response(errors, status=status.HTTP_400_BAD_REQUEST)


# Context helper for override handlers


@dataclass
class OverrideContext:
    """Context object passed to override handlers.

    This provides a convenient way to access common data and utilities
    within override handlers.

    Attributes:
        request: DRF Request object
        user: User instance
        entity: Entity instance
        entry: Entry instance (for retrieve/update/delete operations)
        data: Request data dict (for create/update operations)
        params: Plugin-specific validated parameters from configuration
        plugin_id: ID of the plugin handling this request
        operation: Operation type string
    """

    request: Any  # DRF Request
    user: Any  # User instance
    entity: Any  # Entity instance
    plugin_id: str
    operation: str
    entry: Optional[Any] = None  # Entry instance
    data: Optional[Dict[str, Any]] = None  # Request data
    params: Any = field(default_factory=dict)  # Validated params

    # Deprecated fields kept for backward compatibility
    entity_name: Optional[str] = None  # Use entity.name instead

    def __post_init__(self):
        """Initialize deprecated fields for backward compatibility."""
        if self.entity_name is None and self.entity:
            self.entity_name = self.entity.name

    @property
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        return self.user and self.user.is_authenticated

    def get_request_data(self) -> Dict[str, Any]:
        """Get the request data as a dictionary."""
        if self.data:
            return dict(self.data)
        return dict(self.request.data) if self.request.data else {}


def create_override_context(
    request: Any,
    plugin_id: str,
    entity_name: str,
    operation: str,
    entity: Optional[Any] = None,
    entry: Optional[Any] = None,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Any] = None,
) -> OverrideContext:
    """Create an OverrideContext for a handler.

    Args:
        request: DRF Request object
        plugin_id: ID of the plugin
        entity_name: Name of the entity being operated on (deprecated)
        operation: Operation type
        entity: Entity instance (optional)
        entry: Entry instance (optional)
        data: Request data (optional)
        params: Plugin-specific parameters (optional)

    Returns:
        OverrideContext instance
    """
    return OverrideContext(
        request=request,
        user=request.user,
        entity=entity,
        entry=entry,
        data=data,
        params=params or {},
        plugin_id=plugin_id,
        operation=operation,
        entity_name=entity_name,
    )
