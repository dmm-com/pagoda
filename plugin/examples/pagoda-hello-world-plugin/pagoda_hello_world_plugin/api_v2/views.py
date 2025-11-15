"""
API views for Hello World Plugin

Demonstrates how external plugins can create API endpoints using Pagoda's core libraries.
"""

from datetime import datetime
from typing import Any, Dict

# Import from Pagoda Plugin SDK libraries (fully independent)
from pagoda_plugin_sdk import PluginAPIViewMixin
from pagoda_plugin_sdk.models import Entity, Entry
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


def _get_user_info(request: Request) -> Dict[str, Any]:
    """Extract user information from request.

    Args:
        request: The request object

    Returns:
        Dictionary containing user information
    """
    return {
        "username": request.user.username if request.user.is_authenticated else "anonymous",
        "is_authenticated": request.user.is_authenticated,
    }


def _get_plugin_metadata(**kwargs: Any) -> Dict[str, Any]:
    """Get plugin metadata dictionary.

    Args:
        **kwargs: Additional metadata fields to include

    Returns:
        Dictionary containing plugin metadata
    """
    base_metadata = {
        "id": "hello-world-plugin",
        "name": "Hello World Plugin",
        "version": "1.0.0",
        "type": "external",
        "core": "pagoda-core",
    }
    base_metadata.update(kwargs)
    return base_metadata


def _create_error_response(
    error: str, message: str, status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE
) -> Response:
    """Create standardized error response.

    Args:
        error: Error type/code
        message: Error message
        status_code: HTTP status code

    Returns:
        Response object with error information
    """
    return Response(
        {
            "error": error,
            "message": message,
            "plugin": {
                "id": "hello-world-plugin",
                "name": "Hello World Plugin",
            },
            "timestamp": datetime.now().isoformat(),
        },
        status=status_code,
    )


def _build_entry_data(entry: Any) -> Dict[str, Any]:
    """Build entry data dictionary from Entry model instance.

    Args:
        entry: Entry model instance

    Returns:
        Dictionary containing entry data
    """
    return {
        "id": entry.id,
        "name": entry.name,
        "note": getattr(entry, "note", ""),
        "is_active": entry.is_active,
        "entity": {
            "id": entry.schema.id,
            "name": entry.schema.name,
        }
        if entry.schema
        else None,
        "created_time": entry.created_time.isoformat() if entry.created_time else None,
        "created_user": entry.created_user.username if entry.created_user else None,
        "updated_time": entry.updated_time.isoformat() if entry.updated_time else None,
    }


class HelloView(PluginAPIViewMixin):
    """Simple Hello World API

    Demonstrates basic GET/POST request handling in external plugins.
    """

    def get(self, request: Request) -> Response:
        """Return Hello World message"""
        return Response(
            {
                "message": "Hello from External Hello World Plugin (via pagoda-core)!",
                "plugin": _get_plugin_metadata(),
                "user": _get_user_info(request),
                "pagoda_core_version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
            }
        )

    def post(self, request: Request) -> Response:
        """Execute Hello World job with custom message

        Request body:
            message (str): Custom message (optional)
        """
        message = request.data.get("message", "Hello World!")

        response_data = {
            "message": f"External plugin task would be queued with message: '{message}'",
            "plugin": _get_plugin_metadata(),
            "user": _get_user_info(request),
            "pagoda_core_version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class GreetView(PluginAPIViewMixin):
    """Personalized greeting API

    Returns a greeting for the name specified in the URL parameter.
    """

    def get(self, request: Request, name: str) -> Response:
        """Return a greeting for the specified name

        Args:
            name: Name to greet
        """
        return Response(
            {
                "greeting": f"Hello, {name}! Welcome to Pagoda via External Plugin!",
                "plugin": _get_plugin_metadata(),
                "requested_name": name,
                "user": _get_user_info(request),
                "pagoda_core_version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
            }
        )


class StatusView(PluginAPIViewMixin):
    """Plugin status information API

    Returns basic information and operational status of the plugin.
    """

    def get(self, request: Request) -> Response:
        """Return plugin status information"""
        return Response(
            {
                "plugin": _get_plugin_metadata(
                    status="active",
                    author="Pagoda Development Team",
                    installation="external_package",
                ),
                "system": {
                    "django_app": "pagoda_hello_world_plugin",
                    "package_name": "pagoda-hello-world-plugin",
                    "endpoints": [
                        "/api/v2/plugins/hello-world-plugin/hello/",
                        "/api/v2/plugins/hello-world-plugin/greet/<name>/",
                        "/api/v2/plugins/hello-world-plugin/status/",
                        "/api/v2/plugins/hello-world-plugin/test/",
                    ],
                },
                "user": _get_user_info(request),
                "pagoda_core_version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
            }
        )


class TestView(PluginAPIViewMixin):
    """Authentication-free test endpoint"""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """Test basic plugin functionality without authentication"""
        return Response(
            {
                "message": "External Hello World Plugin is working via pagoda-core!",
                "plugin": _get_plugin_metadata(),
                "test": "no-auth",
                "user": _get_user_info(request),
                "pagoda_core_version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
            }
        )


class EntityListView(PluginAPIViewMixin):
    """Entity list API

    Demonstrates accessing Entity models through the plugin SDK.
    Shows type-safe access to host application models.
    """

    permission_classes = [AllowAny]  # Allow unauthenticated access for testing

    def get(self, request: Request) -> Response:
        """Get list of all active entities

        Returns:
            JSON response with entity list and metadata
        """
        try:
            # Check if Entity model is available
            if Entity is None:
                return _create_error_response(
                    "Entity model not available",
                    "Plugin system may not be initialized",
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # Use Entity model with type safety!
            entities = Entity.objects.filter(is_active=True)

            # Convert to JSON serializable format
            entity_list = []
            for entity in entities:
                entity_data = {
                    "id": entity.id,
                    "name": entity.name,
                    "note": entity.note,
                    "is_active": entity.is_active,
                    "created_time": entity.created_time.isoformat()
                    if entity.created_time
                    else None,
                    "created_user": entity.created_user.username if entity.created_user else None,
                }
                entity_list.append(entity_data)

            return Response(
                {
                    "entities": entity_list,
                    "count": entities.count(),
                    "plugin": _get_plugin_metadata(core="pagoda-plugin-sdk"),
                    "user": _get_user_info(request),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            return _create_error_response(
                "Failed to retrieve entities",
                str(e),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EntityDetailView(PluginAPIViewMixin):
    """Entity detail API

    Demonstrates accessing individual Entity instances.
    """

    permission_classes = [AllowAny]  # Allow unauthenticated access for testing

    def get(self, request: Request, entity_id: int) -> Response:
        """Get details of a specific entity

        Args:
            entity_id: ID of the entity to retrieve

        Returns:
            JSON response with entity details
        """
        try:
            if Entity is None:
                return _create_error_response(
                    "Entity model not available",
                    "Plugin system may not be initialized",
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # Type-safe entity retrieval
            entity = Entity.objects.get(id=entity_id, is_active=True)

            entity_data = {
                "id": entity.id,
                "name": entity.name,
                "note": entity.note,
                "is_active": entity.is_active,
                "created_time": entity.created_time.isoformat() if entity.created_time else None,
                "created_user": entity.created_user.username if entity.created_user else None,
            }

            return Response(
                {
                    "entity": entity_data,
                    "plugin": _get_plugin_metadata(core="pagoda-plugin-sdk"),
                    "user": _get_user_info(request),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Entity.DoesNotExist:
            return _create_error_response(
                f"Entity with ID {entity_id} not found",
                "Entity does not exist or is not active",
                status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return _create_error_response(
                "Failed to retrieve entity",
                str(e),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EntryListView(PluginAPIViewMixin):
    """Entry list API

    Demonstrates accessing Entry models with their Entity relationships.
    """

    permission_classes = [AllowAny]  # Allow unauthenticated access for testing

    def get(self, request: Request) -> Response:
        """Get list of all active entries

        Query parameters:
            entity_id: Filter entries by entity ID
            limit: Limit number of results

        Returns:
            JSON response with entry list and metadata
        """
        try:
            # Check if models are available
            if Entry is None:
                return _create_error_response(
                    "Entry model not available",
                    "Plugin system may not be initialized",
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # Get query parameters
            entity_id = request.GET.get("entity_id")
            limit = request.GET.get("limit")

            # Base queryset - type safe!
            entries = Entry.objects.filter(is_active=True)

            # Apply filters
            if entity_id:
                try:
                    entity_id = int(entity_id)
                    entries = entries.filter(schema_id=entity_id)
                except ValueError:
                    return _create_error_response(
                        "Invalid entity_id parameter",
                        "entity_id must be a valid integer",
                        status.HTTP_400_BAD_REQUEST,
                    )

            # Apply limit
            if limit:
                try:
                    limit = int(limit)
                    entries = entries[:limit]
                except ValueError:
                    return _create_error_response(
                        "Invalid limit parameter",
                        "limit must be a valid integer",
                        status.HTTP_400_BAD_REQUEST,
                    )

            # Convert to JSON - accessing related Entity through schema field
            entry_list = [_build_entry_data(entry) for entry in entries]

            return Response(
                {
                    "entries": entry_list,
                    "count": entries.count() if not limit else len(entry_list),
                    "filters": {
                        "entity_id": entity_id,
                        "limit": limit,
                    },
                    "plugin": _get_plugin_metadata(core="pagoda-plugin-sdk"),
                    "user": _get_user_info(request),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            return _create_error_response(
                "Failed to retrieve entries",
                str(e),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EntryDetailView(PluginAPIViewMixin):
    """Entry detail API with attributes

    Demonstrates accessing Entry attributes using the get_attrs() method.
    """

    permission_classes = [AllowAny]  # Allow unauthenticated access for testing

    def get(self, request: Request, entry_id: int) -> Response:
        """Get details of a specific entry including its attributes

        Args:
            entry_id: ID of the entry to retrieve

        Returns:
            JSON response with entry details and attributes
        """
        try:
            if Entry is None:
                return _create_error_response(
                    "Entry model not available",
                    "Plugin system may not be initialized",
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # Type-safe entry retrieval
            entry = Entry.objects.get(id=entry_id, is_active=True)

            # Use Entry's custom get_attrs method
            entry_data = _build_entry_data(entry)
            entry_data["attributes"] = entry.get_attrs()  # Entry-specific functionality!

            return Response(
                {
                    "entry": entry_data,
                    "plugin": _get_plugin_metadata(core="pagoda-plugin-sdk"),
                    "user": _get_user_info(request),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Entry.DoesNotExist:
            return _create_error_response(
                f"Entry with ID {entry_id} not found",
                "Entry does not exist or is not active",
                status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return _create_error_response(
                "Failed to retrieve entry",
                str(e),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
