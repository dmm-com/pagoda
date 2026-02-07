"""
Batch permission checking for cross-entity operations.

This module provides utilities for checking permissions across multiple entries
efficiently before executing operations.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, List, Optional, Union

if TYPE_CHECKING:
    from pagoda_plugin_sdk.protocols import EntityProtocol, EntryProtocol, UserProtocol


class ACLType(IntEnum):
    """Access control types matching AirOne's ACL system."""

    Nothing = 0
    Readable = 1 << 0
    Writable = 1 << 1
    Full = 1 << 2


@dataclass
class EntryPermission:
    """Permission status for a single entry."""

    entry_id: int
    entity_name: str
    entry_name: str
    required_permission: ACLType
    granted: bool
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        result = {
            "entry_id": self.entry_id,
            "entity_name": self.entity_name,
            "entry_name": self.entry_name,
            "required_permission": self.required_permission.name.lower(),
            "granted": self.granted,
        }
        if self.reason:
            result["reason"] = self.reason
        return result


@dataclass
class PermissionCheckResult:
    """Result of checking permissions for multiple entries."""

    all_granted: bool
    checked_entries: int
    granted_entries: List[EntryPermission] = field(default_factory=list)
    denied_entries: List[EntryPermission] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "all_granted": self.all_granted,
            "checked_entries": self.checked_entries,
            "denied_entries": [e.to_dict() for e in self.denied_entries],
        }


class BatchPermissionChecker:
    """Utility for checking permissions on multiple entries."""

    def __init__(self, user: "UserProtocol"):
        """
        Initialize the permission checker.

        Args:
            user: The user to check permissions for
        """
        self.user = user

    def check_entries(
        self,
        entries: List["EntryProtocol"],
        permission_type: ACLType = ACLType.Readable,
    ) -> PermissionCheckResult:
        """
        Check permissions for a list of entries.

        Args:
            entries: List of entries to check
            permission_type: Required permission level

        Returns:
            PermissionCheckResult with granted and denied entries
        """
        granted: List[EntryPermission] = []
        denied: List[EntryPermission] = []

        for entry in entries:
            entity_name = ""
            if hasattr(entry, "schema"):
                entity_name = entry.schema.name

            has_permission = self._check_single_permission(entry, permission_type)

            perm = EntryPermission(
                entry_id=entry.id,
                entity_name=entity_name,
                entry_name=entry.name,
                required_permission=permission_type,
                granted=has_permission,
                reason=None if has_permission else "Insufficient permissions",
            )

            if has_permission:
                granted.append(perm)
            else:
                denied.append(perm)

        return PermissionCheckResult(
            all_granted=len(denied) == 0,
            checked_entries=len(entries),
            granted_entries=granted,
            denied_entries=denied,
        )

    def check_entry_ids(
        self,
        entry_ids: List[int],
        permission_type: ACLType = ACLType.Readable,
    ) -> PermissionCheckResult:
        """
        Check permissions for entries by their IDs.

        This method requires the Entry model to be available via model injection.

        Args:
            entry_ids: List of entry IDs to check
            permission_type: Required permission level

        Returns:
            PermissionCheckResult with granted and denied entries
        """
        from pagoda_plugin_sdk.models import Entry

        if Entry is None:
            raise RuntimeError("Entry model not available. Ensure model injection is configured.")

        entries = list(Entry.objects.filter(id__in=entry_ids, is_active=True))
        return self.check_entries(entries, permission_type)

    def check_entity_create_permission(
        self,
        entity_names: List[str],
    ) -> PermissionCheckResult:
        """
        Check if user can create entries in specified entities.

        Args:
            entity_names: List of entity names to check

        Returns:
            PermissionCheckResult with granted and denied entity permissions
        """
        from pagoda_plugin_sdk.models import Entity

        if Entity is None:
            raise RuntimeError("Entity model not available. Ensure model injection is configured.")

        granted: List[EntryPermission] = []
        denied: List[EntryPermission] = []

        for entity_name in entity_names:
            try:
                entity = Entity.objects.get(name=entity_name, is_active=True)
                has_permission = self._check_entity_create_permission(entity)

                perm = EntryPermission(
                    entry_id=0,  # No entry yet
                    entity_name=entity_name,
                    entry_name="",
                    required_permission=ACLType.Writable,
                    granted=has_permission,
                    reason=None if has_permission else f"Cannot create entries in {entity_name}",
                )

                if has_permission:
                    granted.append(perm)
                else:
                    denied.append(perm)
            except Exception:
                denied.append(
                    EntryPermission(
                        entry_id=0,
                        entity_name=entity_name,
                        entry_name="",
                        required_permission=ACLType.Writable,
                        granted=False,
                        reason=f"Entity {entity_name} not found",
                    )
                )

        return PermissionCheckResult(
            all_granted=len(denied) == 0,
            checked_entries=len(entity_names),
            granted_entries=granted,
            denied_entries=denied,
        )

    def _check_single_permission(
        self,
        entry: "EntryProtocol",
        permission_type: ACLType,
    ) -> bool:
        """Check permission for a single entry."""
        if hasattr(entry, "may_permitted"):
            return entry.may_permitted(self.user, permission_type)
        if hasattr(self.user, "has_permission"):
            return self.user.has_permission(entry, permission_type)
        # Fallback: assume permission granted if we can't check
        return True

    def _check_entity_create_permission(self, entity: "EntityProtocol") -> bool:
        """Check if user can create entries in an entity."""
        if hasattr(entity, "may_permitted"):
            return entity.may_permitted(self.user, ACLType.Writable)
        if hasattr(self.user, "has_permission"):
            return self.user.has_permission(entity, ACLType.Writable)
        return True


def check_permissions(
    user: "UserProtocol",
    entries: Optional[List["EntryProtocol"]] = None,
    entry_ids: Optional[List[int]] = None,
    entities: Optional[List[str]] = None,
    permission_type: Union[ACLType, str] = ACLType.Readable,
) -> PermissionCheckResult:
    """
    Convenience function for checking permissions.

    Args:
        user: User to check permissions for
        entries: List of entry objects to check
        entry_ids: List of entry IDs to check
        entities: List of entity names for create permission check
        permission_type: Required permission level (ACLType or string)

    Returns:
        PermissionCheckResult
    """
    # Convert string permission type to ACLType
    if isinstance(permission_type, str):
        perm_map = {
            "read": ACLType.Readable,
            "readable": ACLType.Readable,
            "write": ACLType.Writable,
            "writable": ACLType.Writable,
            "full": ACLType.Full,
            "create": ACLType.Writable,
            "delete": ACLType.Full,
        }
        permission_type = perm_map.get(permission_type.lower(), ACLType.Readable)

    checker = BatchPermissionChecker(user)

    if entries:
        return checker.check_entries(entries, permission_type)
    elif entry_ids:
        return checker.check_entry_ids(entry_ids, permission_type)
    elif entities:
        return checker.check_entity_create_permission(entities)
    else:
        return PermissionCheckResult(all_granted=True, checked_entries=0)


class PermissionDeniedError(Exception):
    """Raised when permission check fails for one or more entries."""

    def __init__(
        self,
        message: str = "Permission denied",
        denied_entries: Optional[List[EntryPermission]] = None,
    ):
        super().__init__(message)
        self.denied_entries = denied_entries or []

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "error": "PERMISSION_DENIED",
            "message": str(self),
            "details": {
                "denied_entries": [e.to_dict() for e in self.denied_entries],
            },
        }
