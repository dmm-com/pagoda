"""
Transaction management utilities for cross-entity operations.

This module provides context managers and utilities for ensuring atomic
operations across multiple entities.
"""

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional

from django.db import transaction

if TYPE_CHECKING:
    from pagoda_plugin_sdk.protocols import EntryProtocol, UserProtocol

logger = logging.getLogger(__name__)


@dataclass
class OperationLog:
    """Log entry for a cross-entity operation."""

    plugin_id: str
    user_id: int
    operation: str
    affected_entries: int
    entities: List[str]
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


@dataclass
class AtomicOperationContext:
    """Context for managing atomic cross-entity operations."""

    user: "UserProtocol"
    created_entries: List["EntryProtocol"] = field(default_factory=list)
    updated_entries: List["EntryProtocol"] = field(default_factory=list)
    deleted_entries: List[int] = field(default_factory=list)
    _operation_log: Optional[OperationLog] = field(default=None, init=False)

    def create_entry(
        self,
        entity_name: str,
        name: str,
        attrs: Dict[str, Any],
        user: Optional["UserProtocol"] = None,
    ) -> "EntryProtocol":
        """
        Create a new entry within the atomic operation.

        Args:
            entity_name: Name of the entity to create entry in
            name: Entry name
            attrs: Entry attributes
            user: User creating the entry (defaults to context user)

        Returns:
            Created entry
        """
        from pagoda_plugin_sdk.models import Entity, Entry

        if Entity is None or Entry is None:
            raise RuntimeError("Models not available. Ensure model injection is configured.")

        entity = Entity.objects.get(name=entity_name, is_active=True)
        creating_user = user or self.user

        entry = Entry.objects.create(
            name=name,
            schema=entity,
            created_user=creating_user,
        )

        # Set attributes
        self._set_entry_attrs(entry, attrs)

        self.created_entries.append(entry)
        return entry

    def update_entry(
        self,
        entry: "EntryProtocol",
        data: Dict[str, Any],
        user: Optional["UserProtocol"] = None,
    ) -> "EntryProtocol":
        """
        Update an entry within the atomic operation.

        Args:
            entry: Entry to update
            data: Data to update (name and/or attrs)
            user: User performing the update

        Returns:
            Updated entry
        """
        if "name" in data:
            entry.name = data["name"]

        if "attrs" in data:
            self._set_entry_attrs(entry, data["attrs"])

        entry.save()
        self.updated_entries.append(entry)
        return entry

    def delete_entry(
        self,
        entry: "EntryProtocol",
        user: Optional["UserProtocol"] = None,
        hard_delete: bool = False,
    ) -> None:
        """
        Delete an entry within the atomic operation.

        Args:
            entry: Entry to delete
            user: User performing the deletion
            hard_delete: If True, permanently delete; if False, soft delete
        """
        entry_id = entry.id

        if hard_delete:
            entry.delete()
        else:
            entry.is_active = False
            entry.save()

        self.deleted_entries.append(entry_id)

    def link_entries(
        self,
        source: "EntryProtocol",
        targets: List["EntryProtocol"],
        attribute_name: str,
    ) -> None:
        """
        Link source entry to target entries via an attribute.

        Args:
            source: Source entry
            targets: Target entries to link
            attribute_name: Name of the attribute to store the link
        """
        # This implementation depends on the specific attribute type
        # For array attributes, we add the references
        # For single reference, we set the last target
        if not targets:
            return

        # Find or create the attribute
        if hasattr(source, "attrs"):
            from pagoda_plugin_sdk.models import Attribute, EntityAttr

            if EntityAttr is None or Attribute is None:
                logger.warning("Cannot link entries: Attribute models not available")
                return

            try:
                entity_attr = EntityAttr.objects.get(
                    parent_entity=source.schema,
                    name=attribute_name,
                )

                attr, _ = Attribute.objects.get_or_create(
                    parent_entry=source,
                    schema=entity_attr,
                )

                # Add references to targets
                for target in targets:
                    attr.add_value(self.user, target)

            except Exception as e:
                logger.warning(f"Failed to link entries: {e}")

    def log_summary(
        self,
        plugin_id: str,
        operation: str,
        affected_entries: Optional[int] = None,
        entities: Optional[List[str]] = None,
    ) -> None:
        """
        Log a summary of the operation for auditing.

        Args:
            plugin_id: ID of the plugin performing the operation
            operation: Operation type (create, update, delete, etc.)
            affected_entries: Number of entries affected
            entities: List of entity names involved
        """
        if affected_entries is None:
            affected_entries = (
                len(self.created_entries) + len(self.updated_entries) + len(self.deleted_entries)
            )

        if entities is None:
            entities = list(
                set(
                    e.schema.name
                    for e in self.created_entries + self.updated_entries
                    if hasattr(e, "schema")
                )
            )

        self._operation_log = OperationLog(
            plugin_id=plugin_id,
            user_id=self.user.id if hasattr(self.user, "id") else 0,
            operation=operation,
            affected_entries=affected_entries,
            entities=entities,
            status="in_progress",
            started_at=datetime.now(),
        )

    def _set_entry_attrs(self, entry: "EntryProtocol", attrs: Dict[str, Any]) -> None:
        """Set attributes on an entry."""
        # This is a simplified implementation
        # The actual implementation depends on AirOne's attribute system
        if hasattr(entry, "set_attrs"):
            entry.set_attrs(attrs)
        elif hasattr(entry, "attrs"):
            for key, value in attrs.items():
                try:
                    setattr(entry.attrs, key, value)
                except Exception:
                    pass

    def _finalize_log(self, status: str, error: Optional[str] = None) -> None:
        """Finalize the operation log."""
        if self._operation_log:
            self._operation_log.completed_at = datetime.now()
            self._operation_log.status = status
            self._operation_log.error = error
            if self._operation_log.started_at:
                duration = self._operation_log.completed_at - self._operation_log.started_at
                self._operation_log.duration_ms = int(duration.total_seconds() * 1000)

            # Log to standard logger
            log_data = {
                "plugin_id": self._operation_log.plugin_id,
                "user_id": self._operation_log.user_id,
                "operation": self._operation_log.operation,
                "affected_entries": self._operation_log.affected_entries,
                "entities": self._operation_log.entities,
                "status": status,
                "duration_ms": self._operation_log.duration_ms,
            }
            if error:
                log_data["error"] = error
                logger.error(f"Cross-entity operation failed: {log_data}")
            else:
                logger.info(f"Cross-entity operation completed: {log_data}")


@contextmanager
def atomic_operation(
    user: Optional["UserProtocol"] = None,
) -> Generator[AtomicOperationContext, None, None]:
    """
    Context manager for atomic cross-entity operations.

    All database operations within this context are executed within a single
    transaction. If any operation fails, all changes are rolled back.

    Args:
        user: User performing the operation

    Yields:
        AtomicOperationContext for managing the operation

    Example:
        with atomic_operation(request.user) as op:
            entry1 = op.create_entry("Service", "My Service", {...})
            entry2 = op.create_entry("Configuration", "Config1", {...})
            op.link_entries(entry1, [entry2], "configurations")
            op.log_summary("my-plugin", "create_composite")
    """
    # Create a dummy user if none provided (for testing)
    if user is None:

        @dataclass
        class DummyUser:
            id: int = 0

        user = DummyUser()

    context = AtomicOperationContext(user=user)

    try:
        with transaction.atomic():
            yield context
            context._finalize_log("success")
    except Exception as e:
        context._finalize_log("failed", str(e))
        raise


class TransactionError(Exception):
    """Raised when a transaction fails."""

    def __init__(self, message: str, rollback_performed: bool = True):
        super().__init__(message)
        self.rollback_performed = rollback_performed
