"""
Cross-Entity Sample Plugin class.

This plugin demonstrates cross-entity operations in AirOne using the
pagoda-plugin-sdk with the ID-based endpoint override pattern.

Configure via BACKEND_PLUGIN_ENTITY_OVERRIDES environment variable:
    BACKEND_PLUGIN_ENTITY_OVERRIDES='{"42":{"plugin":"cross-entity-sample","operations":["create","retrieve","update","delete"],"params":{"configuration_entity_id":99}}}'
"""

from typing import Any, Callable, Dict, List, Optional, Set

from pagoda_plugin_sdk import Plugin

from pagoda_cross_entity_sample_plugin.handlers import ServiceHandlers
from pagoda_cross_entity_sample_plugin.relationships import (
    EntityRelationship,
    get_plugin_relationships,
)


class CrossEntityPlugin(Plugin):
    """Sample plugin demonstrating cross-entity operations via endpoint override.

    This plugin provides an example implementation of how to override standard
    Entry API operations to create, read, update, and delete composite entries
    that span multiple entities.

    Key Features:
    - Override entity CRUD operations (configured via BACKEND_PLUGIN_ENTITY_OVERRIDES)
    - Automatic creation of related Configuration entries
    - Atomic cross-entity transactions
    - Permission pre-checking for all affected entries

    Configuration (BACKEND_PLUGIN_ENTITY_OVERRIDES):
        {
            "<entity_id>": {
                "plugin": "cross-entity-sample",
                "operations": ["create", "retrieve", "update", "delete"],
                "params": {
                    "configuration_entity_id": <config_entity_id>,
                    "cascade_delete": true
                }
            }
        }
    """

    id = "cross-entity-sample"
    name = "Cross-Entity Sample Plugin"
    version = "3.0.0"  # ID-based override system
    description = "Demonstrates cross-entity operations with ID-based endpoint override"
    author = "AirOne Team"

    # Django integration (no custom endpoints needed)
    django_apps: List[str] = []

    # Plugin capabilities
    capabilities: Set[str] = {"cross_entity", "composite_entries", "endpoint_override"}

    def __init__(self):
        super().__init__()
        # Initialize handlers
        self._handlers = ServiceHandlers(self)
        # Map operations to handler methods
        self._operation_handlers = {
            "create": self._handlers.handle_create,
            "retrieve": self._handlers.handle_retrieve,
            "update": self._handlers.handle_update,
            "delete": self._handlers.handle_delete,
        }

    def get_relationships(self) -> List[EntityRelationship]:
        """Get entity relationship definitions for this plugin.

        Returns:
            List of EntityRelationship objects
        """
        return get_plugin_relationships()

    def validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize plugin parameters.

        Args:
            params: Raw parameters from configuration

        Returns:
            Validated parameters dict

        Raises:
            ValueError: If required parameters are missing
        """
        # configuration_entity_id is optional but useful for cross-entity ops
        validated = {
            "configuration_entity_id": params.get("configuration_entity_id"),
            "cascade_delete": params.get("cascade_delete", False),
        }
        return validated

    def get_handler(self, operation: str) -> Optional[Callable]:
        """Get the handler for a specific operation.

        Args:
            operation: Operation type (create, retrieve, update, delete)

        Returns:
            Handler callable or None if not supported
        """
        return self._operation_handlers.get(operation.lower())
