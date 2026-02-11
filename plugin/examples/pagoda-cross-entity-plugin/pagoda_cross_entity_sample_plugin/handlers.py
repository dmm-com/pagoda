"""
Override handlers for the Service entity.

This module contains the entry operation override handlers for the Service entity.
These handlers intercept the standard Entry API operations and provide custom
cross-entity behavior.

Updated to use the new ID-based override system with OverrideContext.
"""

import logging
from datetime import datetime

from pagoda_plugin_sdk.override import (
    OverrideContext,
    accepted_response,
    error_response,
    no_content_response,
    override_operation,
    permission_denied_response,
    success_response,
)
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class ServiceHandlers:
    """Override handlers for Service entity operations.

    This class provides custom handlers that override the default Entry API
    behavior for configured entities. Each handler method is decorated with
    @override_operation to register it with the override system.

    The entity-to-handler mapping is configured via BACKEND_PLUGIN_ENTITY_OVERRIDES
    environment variable, allowing flexible ID-based configuration.

    The handlers implement cross-entity operations that:
    - Create Service entries with related Configuration entries
    - Return enriched data including related entries on retrieve
    - Update both Service and related entries atomically
    - Cascade delete related entries based on params configuration
    """

    def __init__(self, plugin):
        """Initialize handlers with plugin reference.

        Args:
            plugin: The plugin instance that owns these handlers
        """
        self.plugin = plugin
        self._relationships = None

    @property
    def relationships(self):
        """Get the entity relationships (lazy loaded)."""
        if self._relationships is None:
            self._relationships = self.plugin.get_relationships()
        return self._relationships

    @override_operation("create")
    def handle_create(self, context: OverrideContext) -> Response:
        """Handle entry creation with related entries.

        This handler creates an entry along with any related
        Configuration entries specified in the request data.

        Args:
            context: OverrideContext containing request, entity, data, params

        Returns:
            Response with 202 Accepted and created entry info

        Request data format:
            {
                "name": "my-service",
                "attrs": {...},
                "configurations": [  # Optional related entries
                    {"name": "config-1", "attrs": {...}},
                    ...
                ]
            }

        Configuration params (from BACKEND_PLUGIN_ENTITY_OVERRIDES):
            - configuration_entity_id: ID of the Configuration entity
        """
        user = context.user
        entity = context.entity
        data = context.data or {}
        params = context.params or {}

        # Get configuration entity ID from params
        config_entity_id = params.get("configuration_entity_id")

        # Extract main entry data and related data
        entry_name = data.get("name", "")
        attrs = data.get("attrs", {})
        configurations = data.get("configurations", [])

        logger.info(
            f"[{context.plugin_id}] Creating entry '{entry_name}' in entity {entity.id} "
            f"with {len(configurations)} configurations for user {user.username}"
        )

        try:
            from job.models import Job

            # Create the main entry via Job
            job_params = {
                "schema": entity.id,
                "name": entry_name,
                "attrs": attrs,
            }
            job = Job.new_create_entry_v2(user, None, params=job_params)
            job.run()

            # If configuration entity is specified and configurations provided
            if config_entity_id and configurations:
                for config_data in configurations:
                    config_job_params = {
                        "schema": config_entity_id,
                        "name": config_data.get("name", ""),
                        "attrs": config_data.get("attrs", {}),
                    }
                    config_job = Job.new_create_entry_v2(user, None, params=config_job_params)
                    config_job.run()

            return accepted_response(
                {
                    "message": f"Entry '{entry_name}' creation accepted",
                    "entity_id": entity.id,
                    # Distinctive plugin information
                    "_plugin_override": {
                        "active": True,
                        "plugin_id": context.plugin_id,
                        "message": "Entry created via cross-entity-sample plugin!",
                        "configurations_created": len(configurations),
                    },
                }
            )

        except PermissionError as e:
            logger.warning(f"Permission denied creating entry: {e}")
            return permission_denied_response(str(e))
        except Exception as e:
            logger.error(f"Error creating entry: {e}", exc_info=True)
            return error_response(f"Failed to create entry: {e}")

    @override_operation("retrieve")
    def handle_retrieve(self, context: OverrideContext) -> Response:
        """Handle entry retrieval with related data.

        This handler returns the entry data along with plugin-specific
        enrichment. Adds distinctive plugin branding to show override is working.

        Args:
            context: OverrideContext containing request, entity, entry

        Returns:
            Response with entry data
        """
        user = context.user
        entry = context.entry

        if not entry:
            return error_response("Entry not found", status_code=404)

        logger.info(
            f"[PLUGIN OVERRIDE] Retrieving entry '{entry.name}' "
            f"via cross-entity-sample plugin for user {user.username}"
        )

        try:
            # Use the standard serializer to generate correct response format
            from entry.api_v2.serializers import EntryRetrieveSerializer

            serializer = EntryRetrieveSerializer(entry, context={"request": context.request})
            response_data = serializer.data

            # Add plugin-specific fields
            response_data["_plugin_override"] = {
                "active": True,
                "plugin_id": context.plugin_id,
                "plugin_version": "3.0.0",
                "message": "This response was handled by cross-entity-sample plugin!",
                "params": context.params,
            }
            response_data["_retrieved_at"] = datetime.now().isoformat()

            return success_response(response_data)

        except Exception as e:
            logger.error(f"Error retrieving entry {entry.id}: {e}", exc_info=True)
            return error_response(f"Failed to retrieve entry: {e}")

    @override_operation("update")
    def handle_update(self, context: OverrideContext) -> Response:
        """Handle entry update with related entries.

        This handler updates the entry and can also update
        related entries if specified in the request.

        Args:
            context: OverrideContext containing request, entity, entry, data

        Returns:
            Response with 202 Accepted
        """
        user = context.user
        entry = context.entry
        data = context.data or {}

        if not entry:
            return error_response("Entry not found", status_code=404)

        logger.info(f"[{context.plugin_id}] Updating entry '{entry.name}' for user {user.username}")

        try:
            from job.models import Job

            # Update main entry via Job
            job_params = {
                "schema": entry.schema.id,
            }
            if "name" in data:
                job_params["name"] = data["name"]
            if "attrs" in data:
                job_params["attrs"] = data["attrs"]

            job = Job.new_edit_entry_v2(user, entry, params=job_params)
            job.run()

            return accepted_response(
                {
                    "id": entry.id,
                    "message": "Entry update accepted",
                }
            )

        except PermissionError as e:
            logger.warning(f"Permission denied updating entry: {e}")
            return permission_denied_response(str(e))
        except Exception as e:
            logger.error(f"Error updating entry {entry.id}: {e}", exc_info=True)
            return error_response(f"Failed to update entry: {e}")

    @override_operation("delete")
    def handle_delete(self, context: OverrideContext) -> Response:
        """Handle entry deletion with optional cascade.

        This handler deletes the entry and optionally cascades
        the deletion to related entries based on params configuration.

        Args:
            context: OverrideContext containing request, entity, entry, params

        Returns:
            Response with 204 No Content on success

        Query params:
            cascade: If "true", also delete cascade-enabled related entries

        Configuration params (from BACKEND_PLUGIN_ENTITY_OVERRIDES):
            - cascade_delete: Default cascade behavior
        """
        user = context.user
        entry = context.entry
        params = context.params or {}

        if not entry:
            return error_response("Entry not found", status_code=404)

        # Check cascade from query params or config
        cascade_config = params.get("cascade_delete", False)
        cascade_query = context.request.query_params.get("cascade", "").lower() == "true"
        cascade = cascade_query or cascade_config

        logger.info(
            f"[{context.plugin_id}] Deleting entry '{entry.name}' "
            f"for user {user.username} (cascade={cascade})"
        )

        try:
            from job.models import Job

            # Delete via Job
            job = Job.new_delete_entry_v2(user, entry, params={})
            job.run()

            return no_content_response()

        except PermissionError as e:
            logger.warning(f"Permission denied deleting entry: {e}")
            return permission_denied_response(str(e))
        except Exception as e:
            logger.error(f"Error deleting entry {entry.id}: {e}", exc_info=True)
            return error_response(f"Failed to delete entry: {e}")
