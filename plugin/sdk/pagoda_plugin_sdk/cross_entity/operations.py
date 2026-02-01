"""
Cross-entity operation coordination.

This module provides the CrossEntityOperation class for coordinating
operations across multiple entities.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pagoda_plugin_sdk.cross_entity.composite import CompositeEntry
from pagoda_plugin_sdk.cross_entity.permissions import (
    ACLType,
    BatchPermissionChecker,
    PermissionCheckResult,
    PermissionDeniedError,
)
from pagoda_plugin_sdk.cross_entity.relationships import EntityRelationship
from pagoda_plugin_sdk.cross_entity.transaction import atomic_operation

if TYPE_CHECKING:
    from pagoda_plugin_sdk.protocols import EntryProtocol, UserProtocol


class OperationType(Enum):
    """Types of cross-entity operations."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class OperationStatus(Enum):
    """Status of a cross-entity operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class OperationEntry:
    """Individual entry within a cross-entity operation."""

    entity_name: str
    entry_id: Optional[int] = None  # None for create operations
    data: Dict[str, Any] = field(default_factory=dict)
    action: OperationType = OperationType.CREATE
    result: Optional["EntryProtocol"] = None


@dataclass
class OperationResult:
    """Result of a cross-entity operation."""

    success: bool
    operation_type: OperationType
    affected_entries: int
    entries: List["EntryProtocol"] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        result: Dict[str, Any] = {
            "success": self.success,
            "operation_type": self.operation_type.value,
            "affected_entries": self.affected_entries,
        }
        if self.error:
            result["error"] = self.error
        return result


class CrossEntityOperation:
    """
    Manages atomic cross-entity operations.

    This class coordinates operations that span multiple entities,
    ensuring atomicity and proper permission checking.
    """

    def __init__(
        self,
        user: "UserProtocol",
        relationships: List[EntityRelationship],
        plugin_id: str = "",
    ):
        """
        Initialize a cross-entity operation.

        Args:
            user: User performing the operation
            relationships: Entity relationship definitions
            plugin_id: ID of the plugin (for logging)
        """
        self.user = user
        self.relationships = relationships
        self.plugin_id = plugin_id
        self.entries: List[OperationEntry] = []
        self.status = OperationStatus.PENDING

    def add_create(
        self,
        entity_name: str,
        data: Dict[str, Any],
    ) -> "CrossEntityOperation":
        """
        Add an entry creation to the operation.

        Args:
            entity_name: Entity to create entry in
            data: Entry data (name and attrs)

        Returns:
            self for method chaining
        """
        self.entries.append(
            OperationEntry(
                entity_name=entity_name,
                data=data,
                action=OperationType.CREATE,
            )
        )
        return self

    def add_update(
        self,
        entity_name: str,
        entry_id: int,
        data: Dict[str, Any],
    ) -> "CrossEntityOperation":
        """
        Add an entry update to the operation.

        Args:
            entity_name: Entity containing the entry
            entry_id: ID of entry to update
            data: Data to update

        Returns:
            self for method chaining
        """
        self.entries.append(
            OperationEntry(
                entity_name=entity_name,
                entry_id=entry_id,
                data=data,
                action=OperationType.UPDATE,
            )
        )
        return self

    def add_delete(
        self,
        entity_name: str,
        entry_id: int,
    ) -> "CrossEntityOperation":
        """
        Add an entry deletion to the operation.

        Args:
            entity_name: Entity containing the entry
            entry_id: ID of entry to delete

        Returns:
            self for method chaining
        """
        self.entries.append(
            OperationEntry(
                entity_name=entity_name,
                entry_id=entry_id,
                action=OperationType.DELETE,
            )
        )
        return self

    def pre_check_permissions(self) -> PermissionCheckResult:
        """
        Pre-check permissions for all entries in the operation.

        Returns:
            PermissionCheckResult with granted and denied entries

        Raises:
            PermissionDeniedError: If any permission check fails
        """
        from pagoda_plugin_sdk.models import Entry

        checker = BatchPermissionChecker(self.user)

        # Check existing entries for update/delete
        entry_ids = [e.entry_id for e in self.entries if e.entry_id is not None]
        if entry_ids and Entry is not None:
            existing_entries = list(Entry.objects.filter(id__in=entry_ids, is_active=True))

            # Map entry_id to required permission
            entry_permissions: Dict[int, ACLType] = {}
            for op_entry in self.entries:
                if op_entry.entry_id:
                    if op_entry.action == OperationType.UPDATE:
                        entry_permissions[op_entry.entry_id] = ACLType.Writable
                    elif op_entry.action == OperationType.DELETE:
                        entry_permissions[op_entry.entry_id] = ACLType.Full

            # Check permissions
            for entry in existing_entries:
                perm_type = entry_permissions.get(entry.id, ACLType.Readable)
                result = checker.check_entries([entry], perm_type)
                if not result.all_granted:
                    return result

        # Check entity permissions for creates
        entity_names = list(
            set(e.entity_name for e in self.entries if e.action == OperationType.CREATE)
        )
        if entity_names:
            result = checker.check_entity_create_permission(entity_names)
            if not result.all_granted:
                return result

        return PermissionCheckResult(
            all_granted=True,
            checked_entries=len(self.entries),
        )

    def execute(self) -> OperationResult:
        """
        Execute the operation atomically.

        Returns:
            OperationResult with operation outcome

        Raises:
            PermissionDeniedError: If permission check fails
            Exception: If operation fails (changes are rolled back)
        """
        self.status = OperationStatus.IN_PROGRESS

        # Pre-check permissions
        perm_result = self.pre_check_permissions()
        if not perm_result.all_granted:
            self.status = OperationStatus.FAILED
            raise PermissionDeniedError(
                "Permission denied for one or more entries",
                perm_result.denied_entries,
            )

        created_entries: List["EntryProtocol"] = []

        try:
            with atomic_operation(self.user) as op:
                for op_entry in self.entries:
                    if op_entry.action == OperationType.CREATE:
                        entry = op.create_entry(
                            entity_name=op_entry.entity_name,
                            name=op_entry.data.get("name", ""),
                            attrs=op_entry.data.get("attrs", {}),
                        )
                        op_entry.result = entry
                        created_entries.append(entry)

                    elif op_entry.action == OperationType.UPDATE:
                        from pagoda_plugin_sdk.models import Entry

                        if Entry is None:
                            raise RuntimeError("Entry model not available")

                        entry = Entry.objects.get(id=op_entry.entry_id, is_active=True)
                        op.update_entry(entry, op_entry.data)
                        op_entry.result = entry
                        created_entries.append(entry)

                    elif op_entry.action == OperationType.DELETE:
                        from pagoda_plugin_sdk.models import Entry

                        if Entry is None:
                            raise RuntimeError("Entry model not available")

                        entry = Entry.objects.get(id=op_entry.entry_id, is_active=True)
                        op.delete_entry(entry)

                # Log the operation
                op.log_summary(
                    plugin_id=self.plugin_id,
                    operation=self._get_operation_type().value,
                )

            self.status = OperationStatus.COMPLETED
            return OperationResult(
                success=True,
                operation_type=self._get_operation_type(),
                affected_entries=len(self.entries),
                entries=created_entries,
            )

        except PermissionDeniedError:
            self.status = OperationStatus.FAILED
            raise
        except Exception as e:
            self.status = OperationStatus.ROLLED_BACK
            return OperationResult(
                success=False,
                operation_type=self._get_operation_type(),
                affected_entries=0,
                error=str(e),
            )

    def _get_operation_type(self) -> OperationType:
        """Determine the primary operation type."""
        if not self.entries:
            return OperationType.READ

        # Return the most "significant" operation type
        has_delete = any(e.action == OperationType.DELETE for e in self.entries)
        has_create = any(e.action == OperationType.CREATE for e in self.entries)
        has_update = any(e.action == OperationType.UPDATE for e in self.entries)

        if has_delete:
            return OperationType.DELETE
        if has_create:
            return OperationType.CREATE
        if has_update:
            return OperationType.UPDATE
        return OperationType.READ

    @classmethod
    def create_composite(
        cls,
        user: "UserProtocol",
        main_entity: str,
        main_data: Dict[str, Any],
        related_data: Dict[str, List[Dict[str, Any]]],
        relationships: List[EntityRelationship],
        plugin_id: str = "",
    ) -> CompositeEntry:
        """
        Create a composite entry with all related entries atomically.

        Args:
            user: User performing the operation
            main_entity: Name of the main entity
            main_data: Data for main entry (name and attrs)
            related_data: Related entries keyed by relationship name
            relationships: Entity relationship definitions
            plugin_id: Plugin ID for logging

        Returns:
            CompositeEntry with created entries
        """
        operation = cls(user, relationships, plugin_id)

        # Add main entry
        operation.add_create(main_entity, main_data)

        # Add related entries
        for rel_name, entries_data in related_data.items():
            # Find the relationship to get target entity
            rel = next((r for r in relationships if r.attribute_name == rel_name), None)
            if rel:
                for entry_data in entries_data:
                    operation.add_create(rel.target_entity, entry_data)

        # Execute
        result = operation.execute()

        if not result.success:
            raise Exception(result.error or "Operation failed")

        # Build composite entry
        main_entry = result.entries[0] if result.entries else None
        if main_entry is None:
            raise Exception("Main entry was not created")

        related_entries: Dict[str, List["EntryProtocol"]] = {}
        idx = 1  # Skip main entry
        for rel_name, entries_data in related_data.items():
            count = len(entries_data)
            related_entries[rel_name] = result.entries[idx : idx + count]
            idx += count

        return CompositeEntry(
            main_entry=main_entry,
            related_entries=related_entries,
            relationships=relationships,
        )
