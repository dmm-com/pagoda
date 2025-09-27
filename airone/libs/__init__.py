"""
AirOne Core Libraries for Plugin Development

This package provides core functionality for external plugins to interact with AirOne.
"""

from .auth import get_current_user_info
from .utils import get_airone_version

__all__ = [
    "get_current_user_info",
    "get_airone_version",
]

__version__ = "1.0.0"
