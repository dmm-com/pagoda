"""
Plugin dispatch mixin for ViewSets.

This module provides a mixin class that automatically dispatches
Entry API operations to plugin override handlers when configured.
"""

import logging
from typing import TYPE_CHECKING, Dict, Optional

from pagoda_plugin_sdk.override import OverrideContext
from rest_framework.request import Request
from rest_framework.response import Response

from airone.plugins.override_manager import OperationType, OverrideRegistration, override_registry

if TYPE_CHECKING:
    from entity.models import Entity
    from entry.models import Entry

logger = logging.getLogger(__name__)


class PluginOverrideMixin:
    """ViewSet mixin that automatically dispatches to plugin override handlers.

    This mixin intercepts ViewSet actions and checks if a plugin has
    registered an override handler for the entity/operation combination.
    If found, the request is dispatched to the plugin handler instead
    of the default ViewSet implementation.

    Usage:
        class EntryAPI(PluginOverrideMixin, viewsets.ModelViewSet):
            ...

    Plugin handlers receive an OverrideContext object containing:
        - request: The DRF request
        - user: The authenticated user
        - entity: The target entity
        - entry: The entry (for retrieve/update/destroy)
        - data: The request data (for create/update)
        - params: Plugin-specific parameters from configuration
    """

    # Type hints for attributes provided by ViewSet (for mypy)
    kwargs: Dict[str, str]

    def _get_override_registration(
        self, entity_id: int, operation: str
    ) -> Optional[OverrideRegistration]:
        """Get override registration for an entity/operation if available."""
        try:
            op_type = OperationType.from_string(operation)
            return override_registry.get_registration(entity_id, op_type)
        except Exception as e:
            logger.warning(f"Error getting override registration: {e}")
            return None

    def _build_override_context(
        self,
        request: Request,
        registration: OverrideRegistration,
        entity: "Entity",
        operation: str,
        entry: Optional["Entry"] = None,
    ) -> OverrideContext:
        """Build the context object for a plugin handler."""
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
            operation=operation,
        )

    def _dispatch_override(
        self,
        request: Request,
        operation: str,
        entity_id: int,
        entity: "Entity",
        entry: Optional["Entry"] = None,
    ) -> Optional[Response]:
        """Attempt to dispatch to a plugin override handler.

        Returns:
            Response from plugin handler, or None if no override registered
        """
        registration = self._get_override_registration(entity_id, operation)
        if not registration:
            return None

        context = self._build_override_context(request, registration, entity, operation, entry)
        try:
            return registration.handler(context)
        except Exception as e:
            logger.error(f"Override handler error for entity {entity_id}/{operation}: {e}")
            raise

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Handle create action with plugin override support."""
        entity_id = self.kwargs.get("entity_id")
        if entity_id:
            from entity.models import Entity

            entity = Entity.objects.filter(id=int(entity_id)).first()
            if entity:
                response = self._dispatch_override(request, "create", entity.id, entity)
                if response is not None:
                    return response

        return super().create(request, *args, **kwargs)  # type: ignore[misc]

    def list(self, request: Request, *args, **kwargs) -> Response:
        """Handle list action with plugin override support."""
        entity_id = self.kwargs.get("entity_id")
        if entity_id:
            from entity.models import Entity

            entity = Entity.objects.filter(id=int(entity_id)).first()
            if entity:
                response = self._dispatch_override(request, "list", entity.id, entity)
                if response is not None:
                    return response

        return super().list(request, *args, **kwargs)  # type: ignore[misc]
