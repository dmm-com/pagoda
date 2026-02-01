"""
Composite entry abstraction for cross-entity operations.

This module provides the CompositeEntry class that represents a main entry
with its related entries across entities.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pagoda_plugin_sdk.cross_entity.relationships import EntityRelationship

if TYPE_CHECKING:
    from pagoda_plugin_sdk.protocols import EntryProtocol


class CompletenessStatus(Enum):
    """Status of composite entry completeness."""

    COMPLETE = "complete"  # All required relationships have entries
    PARTIAL = "partial"  # Some optional relationships missing entries
    INVALID = "invalid"  # Required relationships missing or entries inaccessible


@dataclass
class ValidationResult:
    """Result of validating composite entry completeness."""

    status: CompletenessStatus
    missing_required: List[str] = field(default_factory=list)
    missing_optional: List[str] = field(default_factory=list)
    inaccessible_entries: List[int] = field(default_factory=list)

    @property
    def has_missing_required(self) -> bool:
        """Check if any required relationships are missing."""
        return len(self.missing_required) > 0

    @property
    def is_valid(self) -> bool:
        """Check if the composite is valid for operations."""
        return self.status != CompletenessStatus.INVALID


@dataclass
class CompositeEntry:
    """Logical representation of a main entry with related entries."""

    main_entry: "EntryProtocol"
    related_entries: Dict[str, List["EntryProtocol"]] = field(default_factory=dict)
    relationships: List[EntityRelationship] = field(default_factory=list)

    def get_all_entries(self) -> List["EntryProtocol"]:
        """Returns all entries including main and related."""
        all_entries = [self.main_entry]
        for entries in self.related_entries.values():
            all_entries.extend(entries)
        return all_entries

    def get_all_entry_ids(self) -> List[int]:
        """Returns all entry IDs including main and related."""
        return [e.id for e in self.get_all_entries()]

    def get_entries_by_entity(self, entity_name: str) -> List["EntryProtocol"]:
        """Returns entries belonging to specific entity."""
        result = []
        if hasattr(self.main_entry, "schema") and self.main_entry.schema.name == entity_name:
            result.append(self.main_entry)
        for entries in self.related_entries.values():
            for entry in entries:
                if hasattr(entry, "schema") and entry.schema.name == entity_name:
                    result.append(entry)
        return result

    def get_entries_for_relationship(self, attribute_name: str) -> List["EntryProtocol"]:
        """Returns entries for a specific relationship."""
        return self.related_entries.get(attribute_name, [])

    def validate_completeness(self) -> ValidationResult:
        """Checks if all required related entries exist."""
        missing_required = []
        missing_optional = []

        for rel in self.relationships:
            entries = self.related_entries.get(rel.attribute_name, [])
            if not entries:
                if rel.required:
                    missing_required.append(rel.attribute_name)
                else:
                    missing_optional.append(rel.attribute_name)

        if missing_required:
            status = CompletenessStatus.INVALID
        elif missing_optional:
            status = CompletenessStatus.PARTIAL
        else:
            status = CompletenessStatus.COMPLETE

        return ValidationResult(
            status=status,
            missing_required=missing_required,
            missing_optional=missing_optional,
        )

    def get_cascade_delete_entries(self) -> List["EntryProtocol"]:
        """Returns entries that should be deleted when main entry is deleted."""
        cascade_entries = []
        for rel in self.relationships:
            if rel.cascade_delete:
                cascade_entries.extend(self.related_entries.get(rel.attribute_name, []))
        return cascade_entries

    def to_dict(self, include_attrs: bool = True) -> Dict[str, Any]:
        """Serialize composite entry to dictionary."""
        result: Dict[str, Any] = {
            "id": self.main_entry.id,
            "main_entry": self._entry_to_dict(self.main_entry, include_attrs),
            "related_entries": {},
            "completeness": self.validate_completeness().status.value,
        }

        for rel_name, entries in self.related_entries.items():
            result["related_entries"][rel_name] = [
                self._entry_to_dict(e, include_attrs) for e in entries
            ]

        # Add missing components info
        validation = self.validate_completeness()
        if validation.missing_required or validation.missing_optional:
            result["missing_components"] = validation.missing_required + validation.missing_optional

        return result

    def _entry_to_dict(self, entry: "EntryProtocol", include_attrs: bool = True) -> Dict[str, Any]:
        """Convert a single entry to dictionary."""
        data: Dict[str, Any] = {
            "id": entry.id,
            "name": entry.name,
        }

        if hasattr(entry, "schema"):
            data["entity_name"] = entry.schema.name

        if hasattr(entry, "created_time") and entry.created_time:
            data["created_time"] = entry.created_time.isoformat()

        if include_attrs and hasattr(entry, "get_attrs"):
            try:
                data["attrs"] = entry.get_attrs()
            except Exception:
                data["attrs"] = {}

        return data

    @classmethod
    def from_entry(
        cls,
        entry: "EntryProtocol",
        relationships: List[EntityRelationship],
        fetch_related: bool = True,
    ) -> "CompositeEntry":
        """
        Create a CompositeEntry from an existing entry.

        Args:
            entry: The main entry
            relationships: List of relationship definitions
            fetch_related: Whether to fetch related entries (requires Entry model access)

        Returns:
            CompositeEntry instance
        """
        related_entries: Dict[str, List["EntryProtocol"]] = {}

        if fetch_related:
            related_entries = cls._fetch_related_entries(entry, relationships)

        return cls(
            main_entry=entry,
            related_entries=related_entries,
            relationships=relationships,
        )

    @staticmethod
    def _fetch_related_entries(
        entry: "EntryProtocol",
        relationships: List[EntityRelationship],
    ) -> Dict[str, List["EntryProtocol"]]:
        """
        Fetch related entries based on relationship definitions.

        This method attempts to fetch related entries by examining the entry's
        attributes. The actual implementation depends on how attributes store
        references to other entries.
        """
        related: Dict[str, List["EntryProtocol"]] = {}

        if not hasattr(entry, "attrs"):
            return related

        for rel in relationships:
            attr_name = rel.attribute_name
            related[attr_name] = []

            # Try to get related entries from the entry's attributes
            if hasattr(entry, "get_attrs"):
                try:
                    attrs = entry.get_attrs()
                    if isinstance(attrs, dict) and attr_name in attrs:
                        attr_value = attrs[attr_name]
                        # Handle different attribute value formats
                        if isinstance(attr_value, list):
                            for item in attr_value:
                                if hasattr(item, "id"):
                                    related[attr_name].append(item)
                        elif hasattr(attr_value, "id"):
                            related[attr_name].append(attr_value)
                except Exception:
                    pass

        return related


class IncompleteCompositeError(Exception):
    """Raised when a composite entry is incomplete for the requested operation."""

    def __init__(self, message: str, missing_entries: Optional[List[str]] = None):
        super().__init__(message)
        self.missing_entries = missing_entries or []


class EntryNotAccessibleError(Exception):
    """Raised when an entry in the composite is not accessible."""

    def __init__(self, message: str, entry_id: Optional[int] = None):
        super().__init__(message)
        self.entry_id = entry_id
