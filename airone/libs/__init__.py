"""
AirOne Core Libraries for Plugin Development

This package provides core functionality for external plugins to interact with AirOne.
"""

from .base import Plugin, PluginError, PluginLoadError, PluginValidationError, PluginSecurityError
from .mixins import PluginAPIViewMixin, PluginJobMixin
from .auth import get_current_user_info
from .utils import get_airone_version

__all__ = [
    'Plugin',
    'PluginError',
    'PluginLoadError',
    'PluginValidationError',
    'PluginSecurityError',
    'PluginAPIViewMixin',
    'PluginJobMixin',
    'get_current_user_info',
    'get_airone_version',
]

__version__ = "1.0.0"