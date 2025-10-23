"""
Pagoda Core - Plugin Development Framework

This package provides the core foundation for developing plugins in the Pagoda ecosystem.
It offers base classes, interfaces, and utilities that enable plugins to be completely
independent from the host application.
"""

from .exceptions import (
    PagodaError,
    PluginError,
    PluginLoadError,
    PluginSecurityError,
    PluginValidationError,
)
from .plugin import Plugin
from .utils import get_pagoda_version


# Lazy import for Django-dependent components
def _lazy_import_mixins():
    """Lazy import of Django-dependent mixins"""
    try:
        from .mixins import PluginAPIViewMixin

        return PluginAPIViewMixin
    except ImportError as e:
        if "django" in str(e).lower() or "rest_framework" in str(e).lower():
            raise ImportError(
                "Django and Django REST Framework are required "
                "to use PluginAPIViewMixin. "
                "Please install Django and djangorestframework, "
                "or import this mixin directly when Django is configured."
            )
        raise


def _lazy_import_api():
    """Lazy import of Django REST Framework dependent API components"""
    try:
        from .api import (
            PluginAPIView,
            PluginPagination,
            PluginPermission,
            PluginSerializerMixin,
            PluginViewSet,
        )

        return (
            PluginViewSet,
            PluginAPIView,
            PluginPagination,
            PluginPermission,
            PluginSerializerMixin,
        )
    except ImportError as e:
        if "django" in str(e).lower() or "rest_framework" in str(e).lower():
            raise ImportError(
                "Django and Django REST Framework are required to use API components. "
                "Please install Django and djangorestframework, "
                "or import these components directly when Django is configured."
            )
        raise


# Define lazy properties for mixins and API components
def __getattr__(name):
    if name == "PluginAPIViewMixin":
        return _lazy_import_mixins()
    elif name in (
        "PluginViewSet",
        "PluginAPIView",
        "PluginPagination",
        "PluginPermission",
        "PluginSerializerMixin",
    ):
        api_classes = _lazy_import_api()
        api_names = [
            "PluginViewSet",
            "PluginAPIView",
            "PluginPagination",
            "PluginPermission",
            "PluginSerializerMixin",
        ]
        if name in api_names:
            return api_classes[api_names.index(name)]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__version__ = "1.0.0"

__all__ = [
    # Core classes
    "Plugin",
    # Exceptions
    "PagodaError",
    "PluginError",
    "PluginLoadError",
    "PluginValidationError",
    "PluginSecurityError",
    # Mixins for plugin development
    "PluginAPIViewMixin",
    # API components (Django REST Framework dependent)
    "PluginViewSet",
    "PluginAPIView",
    "PluginPagination",
    "PluginPermission",
    "PluginSerializerMixin",
    # Utilities
    "get_pagoda_version",
]
