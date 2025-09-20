"""
API views for Hello World Plugin

Demonstrates how external plugins can create API endpoints using AirOne's core libraries.
"""

from datetime import datetime

# Import from Pagoda Plugin SDK libraries (fully independent)
from pagoda_plugin_sdk import PluginAPIViewMixin
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class HelloView(PluginAPIViewMixin):
    """Simple Hello World API

    Demonstrates basic GET/POST request handling in external plugins.
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
                    "id": "hello-world-plugin",
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

    def post(self, request):
        """Execute Hello World job with custom message

        Request body:
            message (str): Custom message (optional)
        """
        message = request.data.get("message", "Hello World!")
        user_info = {
            "username": request.user.username if request.user.is_authenticated else "anonymous",
            "is_authenticated": request.user.is_authenticated,
        }

        response_data = {
            "message": f"External plugin task would be queued with message: '{message}'",
            "plugin": {
                "id": "hello-world-plugin",
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
                    "id": "hello-world-plugin",
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
                    "id": "hello-world-plugin",
                    "name": "Hello World Plugin",
                    "version": "1.0.0",
                    "type": "external",
                    "status": "active",
                    "author": "Pagoda Development Team",
                    "installation": "external_package",
                    "core": "pagoda-core",
                },
                "system": {
                    "django_app": "airone_hello_world_plugin",
                    "package_name": "airone-hello-world-plugin",
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
                    "id": "hello-world-plugin",
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
