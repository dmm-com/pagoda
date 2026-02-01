"""
Entity relationship definitions for cross-entity operations.

This module provides classes for defining how entities relate within a plugin context.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class RelationType(Enum):
    """Types of relationships between entities."""

    COMPOSITION = "composition"  # Target is part of source (strong ownership)
    REFERENCE = "reference"  # Source references target (weak link)
    ASSOCIATION = "association"  # Bidirectional relationship


@dataclass
class EntityRelationship:
    """Defines a relationship between entities in a plugin context."""

    source_entity: str
    target_entity: str
    relation_type: RelationType
    attribute_name: str
    cascade_delete: bool = False
    required: bool = True

    def __post_init__(self) -> None:
        """Validate relationship configuration."""
        if not self.source_entity:
            raise ValueError("source_entity cannot be empty")
        if not self.target_entity:
            raise ValueError("target_entity cannot be empty")
        if not self.attribute_name:
            raise ValueError("attribute_name cannot be empty")
        if self.source_entity == self.target_entity:
            raise ValueError("Self-referential relationships are not supported")

    def is_composition(self) -> bool:
        """Check if this is a composition relationship."""
        return self.relation_type == RelationType.COMPOSITION

    def is_reference(self) -> bool:
        """Check if this is a reference relationship."""
        return self.relation_type == RelationType.REFERENCE

    def is_association(self) -> bool:
        """Check if this is an association relationship."""
        return self.relation_type == RelationType.ASSOCIATION


@dataclass
class RelationshipRegistry:
    """Registry for managing entity relationships within a plugin."""

    relationships: List[EntityRelationship] = field(default_factory=list)

    def register(self, relationship: EntityRelationship) -> None:
        """Register a new relationship."""
        # Check for circular references
        if self._creates_cycle(relationship):
            raise CircularReferenceError(
                f"Adding relationship from {relationship.source_entity} to "
                f"{relationship.target_entity} would create a circular reference"
            )
        self.relationships.append(relationship)

    def get_relationships_for_entity(self, entity_name: str) -> List[EntityRelationship]:
        """Get all relationships where entity is the source."""
        return [r for r in self.relationships if r.source_entity == entity_name]

    def get_target_entities(self, source_entity: str) -> List[str]:
        """Get all target entities for a given source entity."""
        return [r.target_entity for r in self.get_relationships_for_entity(source_entity)]

    def get_cascade_delete_targets(self, source_entity: str) -> List[EntityRelationship]:
        """Get relationships that should cascade delete."""
        return [r for r in self.get_relationships_for_entity(source_entity) if r.cascade_delete]

    def _creates_cycle(self, new_relationship: EntityRelationship) -> bool:
        """Check if adding a relationship would create a cycle."""
        visited = set()
        target = new_relationship.target_entity

        def visit(entity: str) -> bool:
            if entity in visited:
                return False
            if entity == new_relationship.source_entity:
                return True
            visited.add(entity)
            for rel in self.get_relationships_for_entity(entity):
                if visit(rel.target_entity):
                    return True
            return False

        return visit(target)


class CircularReferenceError(Exception):
    """Raised when a circular reference is detected in entity relationships."""

    pass
