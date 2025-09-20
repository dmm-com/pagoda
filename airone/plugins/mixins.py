"""
DEPRECATED: This module is deprecated. Use airone.libs.mixins instead.

This module is kept for backward compatibility with sample plugins.
External plugins should use airone.libs.mixins.
"""

# Re-export from airone.libs.mixins for backward compatibility
from ..libs.mixins import PluginAPIViewMixin, PluginJobMixin

__all__ = [
    "PluginAPIViewMixin",
    "PluginJobMixin",
]
