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
from .interfaces import (
    AuthInterface,
    DataInterface,
    EntityDict,
    EntityProtocol,
    EntryDict,
    EntryProtocol,
    HookInterface,
    UserDict,
    UserProtocol,
    serialize_entity,
    serialize_entry,
    serialize_user,
)
from .plugin import Plugin
from .utils import get_pagoda_version


# Lazy import for Django-dependent components
def _lazy_import_mixins():
    """Lazy import of Django-dependent mixins"""
    try:
        from .mixins import PluginAPIViewMixin, PluginJobMixin

        return PluginAPIViewMixin, PluginJobMixin
    except ImportError as e:
        if "django" in str(e).lower() or "rest_framework" in str(e).lower():
            raise ImportError(
                "Django and Django REST Framework are required "
                "to use PluginAPIViewMixin and PluginJobMixin. "
                "Please install Django and djangorestframework, "
                "or import these mixins directly when Django is configured."
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
    if name in ("PluginAPIViewMixin", "PluginJobMixin"):
        mixin_classes = _lazy_import_mixins()
        if name == "PluginAPIViewMixin":
            return mixin_classes[0]
        elif name == "PluginJobMixin":
            return mixin_classes[1]
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
    "PluginJobMixin",
    # API components (Django REST Framework dependent)
    "PluginViewSet",
    "PluginAPIView",
    "PluginPagination",
    "PluginPermission",
    "PluginSerializerMixin",
    # Interfaces for host application interaction
    "AuthInterface",
    "DataInterface",
    "HookInterface",
    # Model protocols
    "EntityProtocol",
    "EntryProtocol",
    "UserProtocol",
    "EntityDict",
    "EntryDict",
    "UserDict",
    "serialize_entity",
    "serialize_entry",
    "serialize_user",
    # Utilities
    "get_pagoda_version",
]
