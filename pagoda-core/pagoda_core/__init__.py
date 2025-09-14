"""
Pagoda Core - Plugin Development Framework

This package provides the core foundation for developing plugins in the Pagoda ecosystem.
It offers base classes, interfaces, and utilities that enable plugins to be completely
independent from the host application.
"""

from .plugin import Plugin
from .exceptions import (
    PagodaError,
    PluginError,
    PluginLoadError,
    PluginValidationError,
    PluginSecurityError,
)
from .interfaces import AuthInterface, DataInterface, HookInterface
from .utils import get_pagoda_version

# Lazy import for Django-dependent components
def _lazy_import_mixins():
    """Lazy import of Django-dependent mixins"""
    try:
        from .mixins import PluginAPIViewMixin, PluginJobMixin
        return PluginAPIViewMixin, PluginJobMixin
    except ImportError as e:
        if 'django' in str(e).lower() or 'rest_framework' in str(e).lower():
            raise ImportError(
                "Django and Django REST Framework are required to use PluginAPIViewMixin and PluginJobMixin. "
                "Please install Django and djangorestframework, or import these mixins directly when Django is configured."
            )
        raise

# Define lazy properties for mixins
def __getattr__(name):
    if name in ('PluginAPIViewMixin', 'PluginJobMixin'):
        mixin_classes = _lazy_import_mixins()
        if name == 'PluginAPIViewMixin':
            return mixin_classes[0]
        elif name == 'PluginJobMixin':
            return mixin_classes[1]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__version__ = "1.0.0"

__all__ = [
    # Core classes
    'Plugin',

    # Exceptions
    'PagodaError',
    'PluginError',
    'PluginLoadError',
    'PluginValidationError',
    'PluginSecurityError',

    # Mixins for plugin development
    'PluginAPIViewMixin',
    'PluginJobMixin',

    # Interfaces for host application interaction
    'AuthInterface',
    'DataInterface',
    'HookInterface',

    # Utilities
    'get_pagoda_version',
]