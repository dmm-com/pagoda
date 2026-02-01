"""
Plugin system for AirOne.

This module provides the plugin integration system that allows external plugins
to be loaded and integrated with the AirOne application.
"""

from .integration import plugin_integration
from .registry import plugin_registry

__all__ = [
    "plugin_integration",
    "plugin_registry",
]
