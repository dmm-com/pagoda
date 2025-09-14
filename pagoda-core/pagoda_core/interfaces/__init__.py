"""
Interfaces for host application integration.

These interfaces define the contract between plugins and host applications.
Host applications must implement these interfaces to provide concrete functionality
to plugins, while plugins use these interfaces to access host application services.
"""

from .auth import AuthInterface
from .data import DataInterface
from .hooks import HookInterface, COMMON_HOOKS

__all__ = [
    'AuthInterface',
    'DataInterface',
    'HookInterface',
    'COMMON_HOOKS',
]