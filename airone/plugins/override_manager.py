"""
Override manager for plugin entry operation overrides.

This module provides the infrastructure for plugins to override
the default behavior of Entry API operations for specific entities.

Changed to ID-based registration with parameter support.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Supported entry operation types that can be overridden."""

    CREATE = "create"
    RETRIEVE = "retrieve"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"

    @classmethod
    def from_string(cls, value: str) -> "OperationType":
        """Convert string to OperationType."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(
                f"Invalid operation type: {value}. Valid types: {[op.value for op in cls]}"
            )


@dataclass
class OverrideRegistration:
    """Registration information for an override handler."""

    entity_id: int
    operation: OperationType
    handler: Callable
    plugin_id: str
    params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0

    def __repr__(self) -> str:
        return (
            f"OverrideRegistration(entity_id={self.entity_id}, "
            f"operation={self.operation.value}, plugin={self.plugin_id})"
        )


class OverrideConflictError(Exception):
    """Raised when multiple plugins try to override the same entity operation."""

    def __init__(
        self,
        entity_id: int,
        operation: str,
        existing_plugin: str,
        new_plugin: str,
    ):
        self.entity_id = entity_id
        self.operation = operation
        self.existing_plugin = existing_plugin
        self.new_plugin = new_plugin
        super().__init__(
            f"Override conflict for entity ID '{entity_id}' operation '{operation}': "
            f"already registered by plugin '{existing_plugin}', "
            f"cannot register for plugin '{new_plugin}'"
        )


class OverrideNotFoundError(Exception):
    """Raised when a referenced override handler is not found."""

    pass


@dataclass
class OverrideRegistry:
    """Registry for plugin entry operation overrides.

    This registry manages the mapping between entity/operation pairs
    and their override handlers provided by plugins.

    Usage:
        registry = OverrideRegistry()

        # Register an override
        registry.register(
            entity_id=42,
            operation=OperationType.CREATE,
            handler=my_handler,
            plugin_id="my-plugin",
            params={"configuration_entity_id": 99},
        )

        # Check for override
        registration = registry.get_registration(42, OperationType.CREATE)
        if registration:
            return registration.handler(context)
    """

    _handlers: Dict[int, Dict[OperationType, OverrideRegistration]] = field(default_factory=dict)
    _initialized: bool = field(default=False)

    def register(
        self,
        entity_id: int,
        operation: OperationType,
        handler: Callable,
        plugin_id: str,
        params: Optional[Dict[str, Any]] = None,
        priority: int = 0,
    ) -> None:
        """Register an override handler for an entity operation.

        Args:
            entity_id: ID of the entity to override
            operation: Operation type to override
            handler: Callable that handles the operation
            plugin_id: ID of the plugin registering the override
            params: Plugin-specific parameters (validated by plugin)
            priority: Priority for future use (not currently implemented)

        Raises:
            OverrideConflictError: If another plugin already registered
                                   an override for this entity/operation
        """
        if entity_id not in self._handlers:
            self._handlers[entity_id] = {}

        # Check for conflicts
        if operation in self._handlers[entity_id]:
            existing = self._handlers[entity_id][operation]
            raise OverrideConflictError(
                entity_id=entity_id,
                operation=operation.value,
                existing_plugin=existing.plugin_id,
                new_plugin=plugin_id,
            )

        registration = OverrideRegistration(
            entity_id=entity_id,
            operation=operation,
            handler=handler,
            plugin_id=plugin_id,
            params=params or {},
            priority=priority,
        )

        self._handlers[entity_id][operation] = registration

        logger.info(
            f"Registered override: entity_id={entity_id}, "
            f"operation='{operation.value}', plugin='{plugin_id}'"
        )

    def unregister(
        self,
        entity_id: int,
        operation: OperationType,
        plugin_id: str,
    ) -> bool:
        """Unregister an override handler.

        Args:
            entity_id: ID of the entity
            operation: Operation type
            plugin_id: ID of the plugin (must match the registered plugin)

        Returns:
            True if unregistered, False if not found
        """
        if entity_id not in self._handlers:
            return False

        if operation not in self._handlers[entity_id]:
            return False

        existing = self._handlers[entity_id][operation]
        if existing.plugin_id != plugin_id:
            logger.warning(
                f"Cannot unregister override for {entity_id}/{operation.value}: "
                f"registered by {existing.plugin_id}, not {plugin_id}"
            )
            return False

        del self._handlers[entity_id][operation]

        # Clean up empty entity entry
        if not self._handlers[entity_id]:
            del self._handlers[entity_id]

        logger.info(
            f"Unregistered override: entity_id={entity_id}, "
            f"operation='{operation.value}', plugin='{plugin_id}'"
        )
        return True

    def unregister_plugin(self, plugin_id: str) -> int:
        """Unregister all overrides for a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            Number of overrides unregistered
        """
        count = 0
        entities_to_clean = []

        for entity_id, operations in self._handlers.items():
            ops_to_remove = []
            for operation, registration in operations.items():
                if registration.plugin_id == plugin_id:
                    ops_to_remove.append(operation)
                    count += 1

            for op in ops_to_remove:
                del operations[op]

            if not operations:
                entities_to_clean.append(entity_id)

        for entity_id in entities_to_clean:
            del self._handlers[entity_id]

        if count > 0:
            logger.info(f"Unregistered {count} overrides for plugin '{plugin_id}'")

        return count

    def get_handler(
        self,
        entity_id: int,
        operation: OperationType,
    ) -> Optional[Callable]:
        """Get the override handler for an entity operation.

        Args:
            entity_id: ID of the entity
            operation: Operation type

        Returns:
            Handler callable if found, None otherwise
        """
        if entity_id not in self._handlers:
            return None

        registration = self._handlers[entity_id].get(operation)
        return registration.handler if registration else None

    def get_registration(
        self,
        entity_id: int,
        operation: OperationType,
    ) -> Optional[OverrideRegistration]:
        """Get the full registration info for an entity operation.

        Args:
            entity_id: ID of the entity
            operation: Operation type

        Returns:
            OverrideRegistration if found, None otherwise
        """
        if entity_id not in self._handlers:
            return None
        return self._handlers[entity_id].get(operation)

    def has_override(
        self,
        entity_id: int,
        operation: Optional[OperationType] = None,
    ) -> bool:
        """Check if an entity has any overrides.

        Args:
            entity_id: ID of the entity
            operation: Specific operation to check (optional)

        Returns:
            True if override exists
        """
        if entity_id not in self._handlers:
            return False

        if operation is None:
            return bool(self._handlers[entity_id])

        return operation in self._handlers[entity_id]

    def get_overridden_entity_ids(self) -> Set[int]:
        """Get all entity IDs that have overrides.

        Returns:
            Set of entity IDs
        """
        return set(self._handlers.keys())

    def get_plugin_overrides(self, plugin_id: str) -> List[OverrideRegistration]:
        """Get all overrides registered by a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            List of OverrideRegistration objects
        """
        result = []
        for operations in self._handlers.values():
            for registration in operations.values():
                if registration.plugin_id == plugin_id:
                    result.append(registration)
        return result

    def get_all_registrations(self) -> List[OverrideRegistration]:
        """Get all override registrations.

        Returns:
            List of all OverrideRegistration objects
        """
        result: List[OverrideRegistration] = []
        for operations in self._handlers.values():
            result.extend(operations.values())
        return result

    def clear(self) -> None:
        """Clear all registrations."""
        self._handlers.clear()
        self._initialized = False
        logger.info("Cleared all override registrations")

    def load_from_settings(
        self,
        settings_config: Dict[str, Any],
        plugin_registry: Any,
    ) -> None:
        """Load override registrations from settings configuration.

        Args:
            settings_config: Dictionary from BACKEND_PLUGIN_ENTITY_OVERRIDES setting
                Format: {
                    "42": {
                        "plugin": "cross-entity-sample",
                        "operations": ["create", "update"],
                        "params": {"configuration_entity_id": 99}
                    }
                }
            plugin_registry: Plugin registry to look up plugins

        Raises:
            ValueError: If configuration is invalid
            OverrideConflictError: If conflicting registrations exist
        """
        for entity_id_str, config in settings_config.items():
            try:
                entity_id = int(entity_id_str)
            except ValueError:
                logger.warning(f"Invalid entity ID in override config: {entity_id_str}")
                continue

            plugin_id = config.get("plugin")
            if not plugin_id:
                logger.warning(f"Missing plugin ID in override config for entity {entity_id}")
                continue

            operations = config.get("operations", [])
            if not operations:
                logger.warning(f"No operations specified in override config for entity {entity_id}")
                continue

            raw_params = config.get("params", {})

            # Get plugin instance from registry
            plugin = plugin_registry.get(plugin_id)
            if not plugin:
                logger.warning(
                    f"Plugin '{plugin_id}' not found for override config on entity {entity_id}"
                )
                continue

            # Validate params using plugin's params model if available
            validated_params = plugin.validate_params(raw_params)

            # Register each operation
            for op_str in operations:
                try:
                    operation = OperationType.from_string(op_str)
                except ValueError as e:
                    logger.warning(
                        f"Invalid operation '{op_str}' in config for entity {entity_id}: {e}"
                    )
                    continue

                # Get the handler from plugin
                handler = plugin.get_handler(op_str)
                if not handler:
                    logger.warning(
                        f"No handler found for operation '{op_str}' in plugin '{plugin_id}'"
                    )
                    continue

                self.register(
                    entity_id=entity_id,
                    operation=operation,
                    handler=handler,
                    plugin_id=plugin_id,
                    params=validated_params,
                )

        self._initialized = True
        count = len(self.get_all_registrations())
        logger.info(f"Loaded {count} override registrations from settings")

    def validate_conflicts(self) -> List[str]:
        """Validate that there are no undetected conflicts.

        This is mainly for debugging and testing purposes.

        Returns:
            List of conflict descriptions (empty if no conflicts)
        """
        # Currently conflicts are detected at registration time,
        # so this always returns empty. Kept for future extensibility.
        return []


# Global registry instance
override_registry = OverrideRegistry()


def get_override_registry() -> OverrideRegistry:
    """Get the global override registry instance.

    Returns:
        The global OverrideRegistry instance
    """
    return override_registry
