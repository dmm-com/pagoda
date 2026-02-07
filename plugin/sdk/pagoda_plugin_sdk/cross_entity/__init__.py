"""Cross-entity relationship definitions for pagoda-plugin-sdk."""

from pagoda_plugin_sdk.cross_entity.relationships import (
    CircularReferenceError,
    EntityRelationship,
    RelationshipRegistry,
    RelationType,
)

__all__ = [
    "EntityRelationship",
    "RelationType",
    "RelationshipRegistry",
    "CircularReferenceError",
]
