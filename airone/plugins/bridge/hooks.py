"""
AirOne Hook System Bridge

Implements pagoda_core.interfaces.HookInterface with AirOne-specific logic.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from pagoda_core.interfaces import HookInterface, COMMON_HOOKS

logger = logging.getLogger(__name__)


class AirOneHookBridge(HookInterface):
    """AirOne-specific implementation of HookInterface

    This bridge connects pagoda-core's hook interface to AirOne's
    plugin system, allowing plugins to register and execute hooks
    within AirOne's lifecycle events.
    """

    def __init__(self):
        self._hooks: Dict[str, List[Dict[str, Any]]] = {}
        self._available_hooks = COMMON_HOOKS.copy()

        # Add AirOne-specific hooks
        self._available_hooks.extend([
            # AirOne-specific entity hooks
            "airone.entity.validation",
            "airone.entity.after_import",
            "airone.entity.before_export",

            # AirOne-specific entry hooks
            "airone.entry.validation",
            "airone.entry.after_import",
            "airone.entry.before_export",

            # AirOne-specific search hooks
            "airone.search.before_query",
            "airone.search.after_query",
            "airone.search.results_filter",

            # AirOne-specific authentication hooks
            "airone.auth.login_success",
            "airone.auth.login_failure",
            "airone.auth.permission_denied",

            # AirOne-specific job hooks
            "airone.job.before_run",
            "airone.job.after_run",
            "airone.job.on_error",
        ])

    def register_hook(self, hook_name: str, callback: Callable, priority: int = 50) -> bool:
        """Register a hook callback in AirOne

        Args:
            hook_name: Name of the hook (e.g., "entry.after_create")
            callback: Callback function to execute
            priority: Execution priority (lower numbers execute first)

        Returns:
            True if registration successful, False otherwise
        """
        if hook_name not in self._available_hooks:
            logger.warning(f"Unknown hook: {hook_name}")
            return False

        if not callable(callback):
            logger.error(f"Hook callback must be callable: {callback}")
            return False

        if hook_name not in self._hooks:
            self._hooks[hook_name] = []

        hook_info = {
            "callback": callback,
            "priority": priority,
            "name": getattr(callback, '__name__', str(callback)),
            "module": getattr(callback, '__module__', 'unknown'),
        }

        # Check if callback is already registered
        for existing in self._hooks[hook_name]:
            if existing['callback'] == callback:
                logger.warning(f"Callback already registered for hook {hook_name}: {callback}")
                return False

        self._hooks[hook_name].append(hook_info)

        # Sort by priority
        self._hooks[hook_name].sort(key=lambda x: x['priority'])

        logger.info(f"Registered hook {hook_name} with callback {hook_info['name']} (priority: {priority})")
        return True

    def unregister_hook(self, hook_name: str, callback: Callable) -> bool:
        """Unregister a hook callback from AirOne

        Args:
            hook_name: Name of the hook
            callback: Callback function to remove

        Returns:
            True if unregistration successful, False otherwise
        """
        if hook_name not in self._hooks:
            return False

        original_count = len(self._hooks[hook_name])
        self._hooks[hook_name] = [
            hook_info for hook_info in self._hooks[hook_name]
            if hook_info['callback'] != callback
        ]

        success = len(self._hooks[hook_name]) < original_count
        if success:
            logger.info(f"Unregistered hook {hook_name} callback: {callback}")

        return success

    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all callbacks registered for a hook in AirOne

        Args:
            hook_name: Name of the hook to execute
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks

        Returns:
            List of results from all callback executions
        """
        if hook_name not in self._hooks:
            return []

        results = []
        callbacks = self._hooks[hook_name]

        logger.debug(f"Executing hook {hook_name} with {len(callbacks)} callbacks")

        for hook_info in callbacks:
            callback = hook_info['callback']
            callback_name = hook_info['name']

            try:
                result = callback(*args, **kwargs)
                results.append(result)
                logger.debug(f"Hook {hook_name} callback {callback_name} executed successfully")
            except Exception as e:
                logger.error(f"Hook {hook_name} callback {callback_name} failed: {e}")
                # Continue executing other callbacks even if one fails
                results.append(None)

        return results

    def get_available_hooks(self) -> List[str]:
        """Get list of available hook names in AirOne

        Returns:
            List of hook names that can be used
        """
        return self._available_hooks.copy()

    def get_hook_callbacks(self, hook_name: str) -> List[Callable]:
        """Get all callbacks registered for a hook

        Args:
            hook_name: Name of the hook

        Returns:
            List of callback functions
        """
        if hook_name not in self._hooks:
            return []

        return [hook_info['callback'] for hook_info in self._hooks[hook_name]]

    def clear_hook_callbacks(self, hook_name: str) -> bool:
        """Clear all callbacks for a hook

        Args:
            hook_name: Name of the hook

        Returns:
            True if successful, False otherwise
        """
        if hook_name not in self._hooks:
            return False

        callback_count = len(self._hooks[hook_name])
        self._hooks[hook_name] = []

        logger.info(f"Cleared {callback_count} callbacks for hook {hook_name}")
        return True

    def get_hook_statistics(self) -> Dict[str, Any]:
        """Get statistics about hook usage

        Returns:
            Dictionary containing hook statistics
        """
        stats = {
            "total_hooks": len(self._available_hooks),
            "registered_hooks": len(self._hooks),
            "total_callbacks": sum(len(callbacks) for callbacks in self._hooks.values()),
            "hook_details": {},
        }

        for hook_name, callbacks in self._hooks.items():
            stats["hook_details"][hook_name] = {
                "callback_count": len(callbacks),
                "callbacks": [
                    {
                        "name": hook_info['name'],
                        "module": hook_info['module'],
                        "priority": hook_info['priority'],
                    }
                    for hook_info in callbacks
                ]
            }

        return stats

    def register_django_signals(self):
        """Register Django signal handlers for common hooks

        This method connects AirOne's Django signals to the hook system,
        allowing plugins to hook into Django model lifecycle events.
        """
        try:
            from django.db.models.signals import post_save, pre_save, post_delete, pre_delete

            def create_signal_handler(hook_name):
                def signal_handler(sender, **kwargs):
                    self.execute_hook(hook_name, sender=sender, **kwargs)
                return signal_handler

            # Connect entry signals if Entry model is available
            try:
                from entry.models import Entry
                post_save.connect(create_signal_handler("entry.after_create"), sender=Entry)
                pre_save.connect(create_signal_handler("entry.before_update"), sender=Entry)
                post_delete.connect(create_signal_handler("entry.after_delete"), sender=Entry)
                logger.info("Connected Entry model signals to hook system")
            except ImportError:
                logger.debug("Entry model not available for signal connection")

            # Connect entity signals if Entity model is available
            try:
                from entity.models import Entity
                post_save.connect(create_signal_handler("entity.after_create"), sender=Entity)
                pre_save.connect(create_signal_handler("entity.before_update"), sender=Entity)
                post_delete.connect(create_signal_handler("entity.after_delete"), sender=Entity)
                logger.info("Connected Entity model signals to hook system")
            except ImportError:
                logger.debug("Entity model not available for signal connection")

        except Exception as e:
            logger.error(f"Error registering Django signals: {e}")