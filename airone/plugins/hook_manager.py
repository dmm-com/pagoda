"""
Hook Manager for Pagoda Plugin System

Manages registration and execution of plugin hooks, integrating with
the legacy custom_view system for backward compatibility.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from .hooks import normalize_hook_name

logger = logging.getLogger(__name__)


class HookManager:
    """Plugin hook execution manager

    This class manages the registration and execution of plugin hooks,
    providing a unified interface for both plugin-based hooks and
    legacy custom_view hooks.
    """

    def __init__(self) -> None:
        """Initialize the hook manager"""
        self._hooks: Dict[str, List[Dict[str, Any]]] = {}
        self._stats: Dict[str, int] = {
            "total_registered": 0,
            "total_executed": 0,
            "total_failed": 0,
        }

    def register_hook(
        self,
        hook_name: str,
        handler: Callable,
        plugin_id: str,
        priority: int = 100,
        entity: Optional[str] = None,
    ) -> None:
        """Register a plugin hook handler

        Args:
            hook_name: Standardized hook name (e.g., 'entry.after_create')
            handler: Callable hook handler function
            plugin_id: ID of the plugin registering this hook
            priority: Execution priority (lower = earlier, default 100)
            entity: Optional entity name filter. If specified, hook only runs for that entity.
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []

        hook_info = {
            "handler": handler,
            "plugin_id": plugin_id,
            "priority": priority,
            "entity": entity,
        }

        self._hooks[hook_name].append(hook_info)
        # Sort by priority (lower number = higher priority)
        self._hooks[hook_name].sort(key=lambda x: x["priority"])

        self._stats["total_registered"] += 1
        entity_info = f" for entity '{entity}'" if entity else ""
        logger.info(
            f"Registered hook '{hook_name}' for plugin '{plugin_id}' "
            f"(priority: {priority}){entity_info}"
        )

    def has_hook(self, handler_name: str, entity_name: Optional[str] = None) -> bool:
        """Check if any plugin registered this hook

        Args:
            handler_name: Hook handler name (can be legacy custom_view name)
            entity_name: Optional entity name for entity-specific hooks

        Returns:
            True if at least one plugin has registered this hook for the given entity
        """
        # Normalize hook name (convert custom_view name to standard name)
        standard_name = normalize_hook_name(handler_name)

        if standard_name not in self._hooks:
            return False

        # Check if any hook matches the entity filter
        for hook_info in self._hooks[standard_name]:
            hook_entity = hook_info.get("entity")
            # Hook matches if:
            # - hook_entity is None (applies to all entities)
            # - entity_name is None (checking if hook exists at all)
            # - hook_entity matches entity_name
            if hook_entity is None or entity_name is None or hook_entity == entity_name:
                return True

        return False

    def execute_hook(
        self, handler_name: str, *args, entity_name: Optional[str] = None, **kwargs
    ) -> List[Any]:
        """Execute all registered plugin hooks for this handler

        Args:
            handler_name: Hook handler name (can be legacy custom_view name)
            *args: Positional arguments to pass to hook handlers
            entity_name: Optional entity name for entity-specific hooks (keyword-only)
            **kwargs: Keyword arguments to pass to hook handlers

        Returns:
            List of results from all hook handlers (in order of priority)
        """
        # Normalize hook name
        standard_name = normalize_hook_name(handler_name)

        if standard_name not in self._hooks:
            return []

        results = []
        hook_list = self._hooks[standard_name]

        # Prepend entity_name to args only for lifecycle hooks
        # (not for data access or validation hooks)
        lifecycle_hooks = {
            "entry.before_create",
            "entry.after_create",
            "entry.before_update",
            "entry.after_update",
            "entry.before_delete",
            "entry.after_delete",
            "entry.before_restore",
            "entry.after_restore",
            "entity.before_create",
            "entity.after_create",
            "entity.before_update",
            "entity.after_update",
        }

        handler_args = args
        if entity_name is not None and standard_name in lifecycle_hooks:
            handler_args = (entity_name,) + args

        for hook_info in hook_list:
            handler = hook_info["handler"]
            plugin_id = hook_info["plugin_id"]
            hook_entity = hook_info.get("entity")

            # Skip if hook is entity-specific and doesn't match
            if hook_entity is not None and entity_name != hook_entity:
                continue

            try:
                result = handler(*handler_args, **kwargs)

                if result is not None:
                    results.append(result)

                self._stats["total_executed"] += 1

            except Exception as e:
                self._stats["total_failed"] += 1
                logger.error(
                    f"Hook '{standard_name}' from plugin '{plugin_id}' failed: {e}",
                    exc_info=True,
                )
                # Continue executing other hooks even if one fails

        return results

    def get_registered_hooks(self) -> List[str]:
        """Get list of all registered hook names

        Returns:
            List of standardized hook names that have handlers registered
        """
        return list(self._hooks.keys())

    def get_hooks_for_plugin(self, plugin_id: str) -> List[str]:
        """Get list of hooks registered by a specific plugin

        Args:
            plugin_id: Plugin ID to query

        Returns:
            List of hook names registered by this plugin
        """
        hooks = []
        for hook_name, hook_list in self._hooks.items():
            for hook_info in hook_list:
                if hook_info["plugin_id"] == plugin_id:
                    hooks.append(hook_name)
                    break
        return hooks

    def get_statistics(self) -> Dict[str, Any]:
        """Get hook execution statistics

        Returns:
            Dictionary containing statistics about hook registration and execution
        """
        return {
            **self._stats,
            "registered_hooks": len(self._hooks),
            "hooks": {hook_name: len(hook_list) for hook_name, hook_list in self._hooks.items()},
        }

    def unregister_plugin_hooks(self, plugin_id: str) -> int:
        """Unregister all hooks for a specific plugin

        Args:
            plugin_id: Plugin ID whose hooks should be unregistered

        Returns:
            Number of hooks unregistered
        """
        count = 0
        for hook_name in list(self._hooks.keys()):
            original_len = len(self._hooks[hook_name])
            self._hooks[hook_name] = [
                hook_info
                for hook_info in self._hooks[hook_name]
                if hook_info["plugin_id"] != plugin_id
            ]
            removed = original_len - len(self._hooks[hook_name])
            count += removed

            # Clean up empty hook lists
            if len(self._hooks[hook_name]) == 0:
                del self._hooks[hook_name]

        if count > 0:
            self._stats["total_registered"] -= count
            logger.info(f"Unregistered {count} hook(s) for plugin '{plugin_id}'")

        return count


# Global hook manager instance
hook_manager = HookManager()
