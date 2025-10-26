"""
Pagoda Hello World Plugin

A sample external plugin demonstrating the Pagoda plugin system capabilities.
"""

from .config import PLUGIN_TASK_CONFIG
from .plugin import HelloWorldPlugin

from airone.lib.plugin_task import PluginTaskRegistry

__version__ = "1.0.0"
__all__ = ["HelloWorldPlugin"]

try:
    PluginTaskRegistry.register(PLUGIN_TASK_CONFIG)
except Exception:
    pass
