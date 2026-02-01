"""
Plugin dispatch mixin for ViewSets.

This module provides a mixin class that automatically dispatches
Entry API operations to plugin override handlers when configured.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from rest_framework.request import Request
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@dataclass
class OverrideContext:
    """Context object passed to override handlers.

    This provides a convenient way to access common data and utilities
    within override handlers.

    Attributes:
        request: DRF Request object
        user: User instance
        entity: Entity instance
        entry: Entry instance (for retrieve/update/delete operations)
        data: Request data dict (for create/update operations)
        params: Plugin-specific validated parameters
        plugin_id: ID of the plugin handling this request
        operation: Operation type string
    """

    request: Any  # DRF Request
    user: Any  # User instance
    entity: Any  # Entity instance
    plugin_id: str
    operation: str
    entry: Optional[Any] = None  # Entry instance
    data: Optional[Dict[str, Any]] = None  # Request data
    params: Any = field(default_factory=dict)  # Validated params (could be dict or Pydantic model)

    @property
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        return self.user and self.user.is_authenticated

    def get_request_data(self) -> Dict[str, Any]:
        """Get the request data as a dictionary."""
        return dict(self.request.data) if self.request.data else {}


class PluginOverrideMixin:
    """ViewSet mixin that automatically dispatches to plugin override handlers.

    This mixin intercepts ViewSet actions and checks if a plugin has
    registered an override handler for the entity/operation combination.
    If found, the request is dispatched to the plugin handler instead
    of the default ViewSet implementation.

    Usage:
        class EntryAPI(PluginOverrideMixin, viewsets.ModelViewSet):
            ...

    The mixin maps ViewSet actions to operation types:
        - create -> CREATE
        - retrieve -> RETRIEVE
        - update -> UPDATE
        - destroy -> DELETE
        - list -> LIST

    Plugin handlers receive an OverrideContext object containing:
        - request: The DRF request
        - user: The authenticated user
        - entity: The target entity
        - entry: The entry (for retrieve/update/destroy)
        - data: The request data (for create/update)
        - params: Plugin-specific parameters from configuration
    """

    # Actions that can be overridden by plugins
    plugin_override_actions = {"create", "retrieve", "update", "destroy", "list"}

    # Map ViewSet actions to operation type strings
    _action_to_operation = {
        "create": "create",
        "retrieve": "retrieve",
        "update": "update",
        "destroy": "delete",
        "list": "list",
    }

    def _get_override_registration(self, entity_id: int, operation: str):
        """Get override registration for an entity/operation if available.

        This function lazily imports the override registry to avoid
        circular imports.

        Args:
            entity_id: ID of the entity
            operation: Operation type string

        Returns:
            OverrideRegistration if found, None otherwise
        """
        try:
            from airone.plugins.override_manager import OperationType, override_registry

            op_type = OperationType.from_string(operation)
            return override_registry.get_registration(entity_id, op_type)
        except ImportError:
            return None
        except Exception as e:
            logger.warning(f"Error getting override registration: {e}")
            return None

    def _get_target_entity_id(self) -> Optional[int]:
        """Get the target entity ID for the current request.

        Override this method if the entity ID is obtained differently.

        Returns:
            Entity ID or None
        """
        # For entry operations, try to get from the entry's schema
        if hasattr(self, "get_object") and self.action in ("retrieve", "update", "destroy"):
            try:
                # Don't call get_object yet - it does permission checks
                # Instead, get the entry from kwargs and lookup
                pk = self.kwargs.get("pk")
                if pk:
                    from entry.models import Entry

                    entry = Entry.objects.filter(pk=pk).select_related("schema").first()
                    if entry:
                        return entry.schema.id
            except Exception:
                pass

        # For create/list, try to get from URL kwargs
        entity_id = self.kwargs.get("entity_id")
        if entity_id:
            return int(entity_id)

        return None

    def _get_entity(self, entity_id: int):
        """Get the Entity instance.

        Args:
            entity_id: Entity ID

        Returns:
            Entity instance or None
        """
        try:
            from entity.models import Entity

            return Entity.objects.get(id=entity_id)
        except Exception:
            return None

    def _get_entry_for_action(self):
        """Get the Entry instance for retrieve/update/destroy actions.

        Returns:
            Entry instance or None
        """
        if self.action not in ("retrieve", "update", "destroy"):
            return None

        try:
            pk = self.kwargs.get("pk")
            if pk:
                from entry.models import Entry

                return Entry.objects.select_related("schema").get(pk=pk)
        except Exception:
            pass
        return None

    def _build_override_context(
        self,
        request: Request,
        registration,
        entity,
        entry=None,
    ) -> OverrideContext:
        """Build the context object for a plugin handler.

        Args:
            request: DRF Request
            registration: OverrideRegistration instance
            entity: Entity instance
            entry: Entry instance (optional)

        Returns:
            OverrideContext instance
        """
        data = None
        if request.method in ("POST", "PUT", "PATCH"):
            data = dict(request.data) if request.data else {}

        return OverrideContext(
            request=request,
            user=request.user,
            entity=entity,
            entry=entry,
            data=data,
            params=registration.params,
            plugin_id=registration.plugin_id,
            operation=self._action_to_operation.get(self.action, self.action),
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Handle create action with plugin override support."""
        entity_id = self._get_target_entity_id()
        if entity_id:
            registration = self._get_override_registration(entity_id, "create")
            if registration:
                entity = self._get_entity(entity_id)
                if entity:
                    context = self._build_override_context(request, registration, entity)
                    try:
                        return registration.handler(context)
                    except Exception as e:
                        logger.error(f"Override handler error for entity {entity_id}/create: {e}")
                        raise

        return super().create(request, *args, **kwargs)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Handle retrieve action with plugin override support."""
        entry = self._get_entry_for_action()
        if entry:
            entity_id = entry.schema.id
            registration = self._get_override_registration(entity_id, "retrieve")
            if registration:
                context = self._build_override_context(request, registration, entry.schema, entry)
                try:
                    return registration.handler(context)
                except Exception as e:
                    logger.error(f"Override handler error for entity {entity_id}/retrieve: {e}")
                    raise

        return super().retrieve(request, *args, **kwargs)

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Handle update action with plugin override support."""
        entry = self._get_entry_for_action()
        if entry:
            entity_id = entry.schema.id
            registration = self._get_override_registration(entity_id, "update")
            if registration:
                context = self._build_override_context(request, registration, entry.schema, entry)
                try:
                    return registration.handler(context)
                except Exception as e:
                    logger.error(f"Override handler error for entity {entity_id}/update: {e}")
                    raise

        return super().update(request, *args, **kwargs)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Handle destroy action with plugin override support."""
        entry = self._get_entry_for_action()
        if entry:
            entity_id = entry.schema.id
            registration = self._get_override_registration(entity_id, "delete")
            if registration:
                context = self._build_override_context(request, registration, entry.schema, entry)
                try:
                    return registration.handler(context)
                except Exception as e:
                    logger.error(f"Override handler error for entity {entity_id}/delete: {e}")
                    raise

        return super().destroy(request, *args, **kwargs)

    def list(self, request: Request, *args, **kwargs) -> Response:
        """Handle list action with plugin override support."""
        entity_id = self._get_target_entity_id()
        if entity_id:
            registration = self._get_override_registration(entity_id, "list")
            if registration:
                entity = self._get_entity(entity_id)
                if entity:
                    context = self._build_override_context(request, registration, entity)
                    try:
                        return registration.handler(context)
                    except Exception as e:
                        logger.error(f"Override handler error for entity {entity_id}/list: {e}")
                        raise

        return super().list(request, *args, **kwargs)
