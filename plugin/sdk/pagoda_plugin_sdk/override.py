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

from dataclasses import dataclass, field
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, TypeVar

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

if TYPE_CHECKING:
    from entity.models import Entity
    from entry.models import Entry
    from user.models import User

# Type variable for decorated methods
F = TypeVar("F", bound=Callable[..., Any])

# Attribute name for storing override metadata on decorated methods
OVERRIDE_META_ATTR = "_override_meta"

_VALID_OPERATIONS = {"create", "retrieve", "update", "delete", "list", "background"}


@dataclass
class OverrideMeta:
    """Metadata for an override handler method."""

    operation: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
        }


def override_operation(operation: str) -> Callable[[F], F]:
    """Decorator to mark a plugin method as an entry operation override.

    This decorator attaches metadata to the method that will be used
    during plugin registration to set up the override handler.

    Entity binding is done via BACKEND_PLUGIN_ENTITY_OVERRIDES configuration.

    Args:
        operation: Operation type to override ("create", "retrieve", "update", "delete", "list")

    Returns:
        Decorated method with override metadata attached

    Example:
        class MyPlugin(Plugin):
            @override_operation("create")
            def handle_create(self, context: OverrideContext):
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
    if operation.lower() not in _VALID_OPERATIONS:
        raise ValueError(
            f"Invalid operation: {operation}. Valid operations: {sorted(_VALID_OPERATIONS)}"
        )

    def decorator(method: F) -> F:
        meta = OverrideMeta(operation=operation.lower())
        setattr(method, OVERRIDE_META_ATTR, meta)

        @wraps(method)
        def wrapper(*args, **kwargs):
            return method(*args, **kwargs)

        setattr(wrapper, OVERRIDE_META_ATTR, meta)
        return wrapper  # type: ignore

    return decorator


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
    data: Dict[str, Any] = {"error": message}
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
    errors: Dict[str, Any] | List[str] | str,
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

    request: Request
    user: "User"
    entity: "Entity"
    plugin_id: str
    operation: str
    entry: Optional["Entry"] = None
    data: Optional[Dict[str, Any]] = None
    params: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        return self.user and self.user.is_authenticated

    def get_request_data(self) -> Dict[str, Any]:
        """Get the request data as a dictionary."""
        if self.data:
            return dict(self.data)
        return dict(self.request.data) if self.request.data else {}
