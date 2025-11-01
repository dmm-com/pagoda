"""
API views for Hello World Plugin

Demonstrates how external plugins can create API endpoints using Pagoda's core libraries.
"""

from datetime import datetime

# Import from Pagoda Plugin SDK libraries (fully independent)
from pagoda_plugin_sdk import PluginAPIViewMixin
from pagoda_plugin_sdk.models import Entity, Entry
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from airone.lib.plugin_task import PluginTaskRegistry
from job.models import Job


class HelloView(PluginAPIViewMixin):
    """Simple Hello World API

    Demonstrates how external plugins can create API endpoints using Pagoda's core libraries.
    """

    def get(self, request):
        """Return Hello World message"""
        # Basic user info (plugin should use interfaces in production)
        user_info = {
            "username": request.user.username if request.user.is_authenticated else "anonymous",
            "is_authenticated": request.user.is_authenticated,
        }

        return Response(
            {
                "message": "Hello from External Hello World Plugin (via pagoda-core)!",
                "plugin": {
                    "id": "hello-world",
                    "name": "Hello World Plugin",
                    "version": "1.0.0",
                    "type": "external",
                    "core": "pagoda-core",
                },
                "user": user_info,
                "pagoda_core_version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
            }
        )


class TaskView(PluginAPIViewMixin):
    """Task execution endpoint for Hello World Plugin

    Queues and executes the hello_world_task.
    """

    def post(self, request):
        """Execute Hello World task with custom message

        Request body:
            message (str): Custom message (optional)
        """
        message = request.data.get("message", "Hello World!")
        user_info = {
            "username": request.user.username if request.user.is_authenticated else "anonymous",
            "is_authenticated": request.user.is_authenticated,
        }

        try:
            operation_id = PluginTaskRegistry.get_operation_id("hello-world", "hello_world_task")

            job = Job._create_new_job(
                user=request.user,
                target=None,
                operation=operation_id,
                text=f"Hello World task: {message}",
                params={"message": message},
            )
            job.run()

            response_data = {
                "message": "Hello World task queued successfully",
                "task_message": message,
                "job_id": job.id,
                "job_status": job.status,
                "plugin": {
                    "id": "hello-world",
                    "name": "Hello World Plugin",
                    "version": "1.0.0",
                    "type": "external",
                    "core": "pagoda-core",
                },
                "user": user_info,
                "pagoda_core_version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {
                    "error": "Failed to queue task",
                    "message": str(e),
                    "plugin": {
                        "id": "hello-world",
                        "name": "Hello World Plugin",
                    },
                    "timestamp": datetime.now().isoformat(),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GreetView(PluginAPIViewMixin):
    """Personalized greeting API

    Returns a greeting for the name specified in the URL parameter.
    """

    def get(self, request, name):
        """Return a greeting for the specified name

        Args:
            name (str): Name to greet
        """
        user_info = {
            "username": request.user.username if request.user.is_authenticated else "anonymous",
            "is_authenticated": request.user.is_authenticated,
        }

        return Response(
            {
                "greeting": f"Hello, {name}! Welcome to Pagoda via External Plugin!",
                "plugin": {
                    "id": "hello-world",
                    "name": "Hello World Plugin",
                    "version": "1.0.0",
                    "type": "external",
                    "core": "pagoda-core",
                },
                "requested_name": name,
                "user": user_info,
                "pagoda_core_version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
            }
        )


class StatusView(PluginAPIViewMixin):
    """Plugin status information API

    Returns basic information and operational status of the plugin.
    """

    def get(self, request):
        """Return plugin status information"""
        user_info = {
            "username": request.user.username if request.user.is_authenticated else "anonymous",
            "is_authenticated": request.user.is_authenticated,
        }

        return Response(
            {
                "plugin": {
                    "id": "hello-world",
                    "name": "Hello World Plugin",
                    "version": "1.0.0",
                    "type": "external",
                    "status": "active",
                    "author": "Pagoda Development Team",
                    "installation": "external_package",
                    "core": "pagoda-core",
                },
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
                "user": user_info,
                "pagoda_core_version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
            }
        )


class TestView(PluginAPIViewMixin):
    """Authentication-free test endpoint"""

    permission_classes = [AllowAny]

    def get(self, request):
        """Test basic plugin functionality without authentication"""
        user_info = {
            "username": request.user.username if request.user.is_authenticated else "anonymous",
            "is_authenticated": request.user.is_authenticated,
        }

        return Response(
            {
                "message": "External Hello World Plugin is working via pagoda-core!",
                "plugin": {
                    "id": "hello-world",
                    "name": "Hello World Plugin",
                    "version": "1.0.0",
                    "type": "external",
                    "core": "pagoda-core",
                },
                "test": "no-auth",
                "user": user_info,
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

    def get(self, request):
        """Get list of all active entities

        Returns:
            JSON response with entity list and metadata
        """
        try:
            # Check if Entity model is available
            if Entity is None:
                return Response(
                    {
                        "error": "Entity model not available",
                        "message": "Plugin system may not be initialized",
                        "plugin": {
                            "id": "hello-world",
                            "name": "Hello World Plugin",
                        },
                        "timestamp": datetime.now().isoformat(),
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
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

            user_info = {
                "username": request.user.username if request.user.is_authenticated else "anonymous",
                "is_authenticated": request.user.is_authenticated,
            }

            return Response(
                {
                    "entities": entity_list,
                    "count": entities.count(),
                    "plugin": {
                        "id": "hello-world",
                        "name": "Hello World Plugin",
                        "version": "1.0.0",
                        "type": "external",
                        "core": "pagoda-plugin-sdk",
                    },
                    "user": user_info,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            return Response(
                {
                    "error": "Failed to retrieve entities",
                    "message": str(e),
                    "plugin": {
                        "id": "hello-world",
                        "name": "Hello World Plugin",
                    },
                    "timestamp": datetime.now().isoformat(),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EntityDetailView(PluginAPIViewMixin):
    """Entity detail API

    Demonstrates accessing individual Entity instances.
    """

    permission_classes = [AllowAny]  # Allow unauthenticated access for testing

    def get(self, request, entity_id):
        """Get details of a specific entity

        Args:
            entity_id: ID of the entity to retrieve

        Returns:
            JSON response with entity details
        """
        try:
            if Entity is None:
                return Response(
                    {"error": "Entity model not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
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

            user_info = {
                "username": request.user.username if request.user.is_authenticated else "anonymous",
                "is_authenticated": request.user.is_authenticated,
            }

            return Response(
                {
                    "entity": entity_data,
                    "plugin": {
                        "id": "hello-world",
                        "name": "Hello World Plugin",
                        "version": "1.0.0",
                        "type": "external",
                        "core": "pagoda-plugin-sdk",
                    },
                    "user": user_info,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Entity.DoesNotExist:
            return Response(
                {"error": f"Entity with ID {entity_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": "Failed to retrieve entity", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EntryListView(PluginAPIViewMixin):
    """Entry list API

    Demonstrates accessing Entry models with their Entity relationships.
    """

    permission_classes = [AllowAny]  # Allow unauthenticated access for testing

    def get(self, request):
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
                return Response(
                    {"error": "Entry model not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
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
                    return Response(
                        {"error": "Invalid entity_id parameter"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Apply limit
            if limit:
                try:
                    limit = int(limit)
                    entries = entries[:limit]
                except ValueError:
                    return Response(
                        {"error": "Invalid limit parameter"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Convert to JSON - accessing related Entity through schema field
            entry_list = []
            for entry in entries:
                entry_data = {
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
                entry_list.append(entry_data)

            user_info = {
                "username": request.user.username if request.user.is_authenticated else "anonymous",
                "is_authenticated": request.user.is_authenticated,
            }

            return Response(
                {
                    "entries": entry_list,
                    "count": entries.count() if not limit else len(entry_list),
                    "filters": {
                        "entity_id": entity_id,
                        "limit": limit,
                    },
                    "plugin": {
                        "id": "hello-world",
                        "name": "Hello World Plugin",
                        "version": "1.0.0",
                        "type": "external",
                        "core": "pagoda-plugin-sdk",
                    },
                    "user": user_info,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            return Response(
                {
                    "error": "Failed to retrieve entries",
                    "message": str(e),
                    "plugin": {
                        "id": "hello-world",
                        "name": "Hello World Plugin",
                    },
                    "timestamp": datetime.now().isoformat(),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EntryDetailView(PluginAPIViewMixin):
    """Entry detail API with attributes

    Demonstrates accessing Entry attributes using the get_attrs() method.
    """

    permission_classes = [AllowAny]  # Allow unauthenticated access for testing

    def get(self, request, entry_id):
        """Get details of a specific entry including its attributes

        Args:
            entry_id: ID of the entry to retrieve

        Returns:
            JSON response with entry details and attributes
        """
        try:
            if Entry is None:
                return Response(
                    {"error": "Entry model not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # Type-safe entry retrieval
            entry = Entry.objects.get(id=entry_id, is_active=True)

            # Use Entry's custom get_attrs method
            attrs = entry.get_attrs()

            entry_data = {
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
                "attributes": attrs,  # Entry-specific functionality!
                "created_time": entry.created_time.isoformat() if entry.created_time else None,
                "created_user": entry.created_user.username if entry.created_user else None,
                "updated_time": entry.updated_time.isoformat() if entry.updated_time else None,
            }

            user_info = {
                "username": request.user.username if request.user.is_authenticated else "anonymous",
                "is_authenticated": request.user.is_authenticated,
            }

            return Response(
                {
                    "entry": entry_data,
                    "plugin": {
                        "id": "hello-world",
                        "name": "Hello World Plugin",
                        "version": "1.0.0",
                        "type": "external",
                        "core": "pagoda-plugin-sdk",
                    },
                    "user": user_info,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Entry.DoesNotExist:
            return Response(
                {"error": f"Entry with ID {entry_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": "Failed to retrieve entry", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
