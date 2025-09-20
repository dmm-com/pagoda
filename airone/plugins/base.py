"""
DEPRECATED: This module is deprecated. Use airone.libs.base instead.

This module is kept for backward compatibility with sample plugins.
External plugins should use airone.libs.base.
"""

# Re-export from airone.libs.base for backward compatibility
from ..libs.base import (
    Plugin,
    PluginError,
    PluginLoadError,
    PluginSecurityError,
    PluginValidationError,
)

__all__ = [
    "Plugin",
    "PluginError",
    "PluginLoadError",
    "PluginValidationError",
    "PluginSecurityError",
]
