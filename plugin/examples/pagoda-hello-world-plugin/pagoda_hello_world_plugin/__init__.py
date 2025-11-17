"""
Pagoda Hello World Plugin

A sample external plugin demonstrating the Pagoda plugin system capabilities.
"""

from .plugin import HelloWorldPlugin

__version__ = "1.0.0"
__all__ = ["HelloWorldPlugin"]

# Note: Plugin task registration is handled in apps.py ready() method
# to avoid circular import issues during Django initialization
