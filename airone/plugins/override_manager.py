"""
Override manager for plugin entry operation overrides.

This module provides the infrastructure for plugins to override
the default behavior of Entry API operations for specific entities.

Changed to ID-based registration with parameter support.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Protocol

if TYPE_CHECKING:
    from pagoda_plugin_sdk.plugin import Plugin


class PluginRegistryProtocol(Protocol):
    """Protocol for plugin registry lookup."""

    def get(self, plugin_id: str) -> Optional["Plugin"]: ...


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
    ) -> None:
        """Register an override handler for an entity operation.

        Args:
            entity_id: ID of the entity to override
            operation: Operation type to override
            handler: Callable that handles the operation
            plugin_id: ID of the plugin registering the override
            params: Plugin-specific parameters (validated by plugin)

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
        )

        self._handlers[entity_id][operation] = registration

        logger.info(
            f"Registered override: entity_id={entity_id}, "
            f"operation='{operation.value}', plugin='{plugin_id}'"
        )

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

    def clear(self) -> None:
        """Clear all registrations."""
        self._handlers.clear()
        self._initialized = False
        logger.info("Cleared all override registrations")

    def load_from_settings(
        self,
        settings_config: Dict[str, Dict[str, Any]],
        plugin_registry: PluginRegistryProtocol,
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
        count = sum(len(ops) for ops in self._handlers.values())
        logger.info(f"Loaded {count} override registrations from settings")


# Global registry instance
override_registry = OverrideRegistry()
