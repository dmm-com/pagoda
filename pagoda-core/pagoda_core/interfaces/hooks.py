"""
Hook Interface.

This interface defines how plugins can register and execute hooks to extend
the host application's functionality at specific extension points.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class HookInterface(ABC):
    """Interface for hook system services

    Host applications must implement this interface to provide hook registration
    and execution services to plugins.
    """

    @abstractmethod
    def register_hook(self, hook_name: str, callback: Callable, priority: int = 50) -> bool:
        """Register a hook callback

        Args:
            hook_name: Name of the hook (e.g., "entry.after_create")
            callback: Callback function to execute
            priority: Execution priority (lower numbers execute first)

        Returns:
            True if registration successful, False otherwise
        """
        pass

    @abstractmethod
    def unregister_hook(self, hook_name: str, callback: Callable) -> bool:
        """Unregister a hook callback

        Args:
            hook_name: Name of the hook
            callback: Callback function to remove

        Returns:
            True if unregistration successful, False otherwise
        """
        pass

    @abstractmethod
    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all callbacks registered for a hook

        Args:
            hook_name: Name of the hook to execute
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks

        Returns:
            List of results from all callback executions
        """
        pass

    @abstractmethod
    def get_available_hooks(self) -> List[str]:
        """Get list of available hook names

        Returns:
            List of hook names that can be used
        """
        pass

    def hook_exists(self, hook_name: str) -> bool:
        """Check if a hook exists

        Args:
            hook_name: Name of the hook to check

        Returns:
            True if hook exists, False otherwise

        Note:
            Default implementation checks available hooks.
            Host applications can override for more efficient checking.
        """
        return hook_name in self.get_available_hooks()

    def get_hook_callbacks(self, hook_name: str) -> List[Callable]:
        """Get all callbacks registered for a hook

        Args:
            hook_name: Name of the hook

        Returns:
            List of callback functions

        Note:
            Default implementation returns empty list.
            Host applications should override this for hook introspection.
        """
        return []

    def clear_hook_callbacks(self, hook_name: str) -> bool:
        """Clear all callbacks for a hook

        Args:
            hook_name: Name of the hook

        Returns:
            True if successful, False otherwise

        Note:
            Default implementation returns False.
            Host applications should override this for hook management.
        """
        return False


# Common hook names that host applications might implement
COMMON_HOOKS = [
    # Entity lifecycle hooks
    "entity.before_create",
    "entity.after_create",
    "entity.before_update",
    "entity.after_update",
    "entity.before_delete",
    "entity.after_delete",

    # Entry lifecycle hooks
    "entry.before_create",
    "entry.after_create",
    "entry.before_update",
    "entry.after_update",
    "entry.before_delete",
    "entry.after_delete",

    # Attribute lifecycle hooks
    "attribute.before_create",
    "attribute.after_create",
    "attribute.before_update",
    "attribute.after_update",
    "attribute.before_delete",
    "attribute.after_delete",

    # User/Authentication hooks
    "user.after_login",
    "user.after_logout",
    "user.before_permission_check",

    # System hooks
    "system.startup",
    "system.shutdown",

    # Custom processing hooks
    "data.before_import",
    "data.after_import",
    "data.before_export",
    "data.after_export",
]