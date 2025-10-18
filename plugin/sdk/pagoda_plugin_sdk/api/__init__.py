"""
API components for plugin development.

This module provides base classes, mixins, and utilities for creating
REST API endpoints in pagoda-core plugins. These components integrate
with Django REST Framework and provide standardized patterns for
authentication, permissions, pagination, and error handling.
"""

from .base import PluginAPIView, PluginViewSet
from .pagination import PluginPagination
from .permissions import PluginPermission
from .serializers import PluginSerializerMixin

__all__ = [
    "PluginViewSet",
    "PluginAPIView",
    "PluginPagination",
    "PluginPermission",
    "PluginSerializerMixin",
]
