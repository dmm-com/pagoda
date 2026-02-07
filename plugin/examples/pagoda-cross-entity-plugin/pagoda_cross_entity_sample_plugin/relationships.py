"""
Entity relationship definitions for the cross-entity sample plugin.

This module defines the relationships between entities that this plugin manages.
In this example, we define a Service entity that has related Configurations.
"""

from dataclasses import dataclass
from enum import Enum


class RelationType(str, Enum):
    """Types of relationships between entities."""

    COMPOSITION = "composition"
    REFERENCE = "reference"


@dataclass
class EntityRelationship:
    """Defines a relationship between two entities."""

    source_entity: str
    target_entity: str
    relation_type: RelationType
    attribute_name: str
    cascade_delete: bool = False
    required: bool = False


# Define relationships for the sample plugin
# Service -> Configuration (composition: configurations are part of a service)
SERVICE_CONFIGURATION_RELATIONSHIP = EntityRelationship(
    source_entity="Service",
    target_entity="Configuration",
    relation_type=RelationType.COMPOSITION,
    attribute_name="configurations",
    cascade_delete=True,
    required=False,
)

# Service -> Environment (reference: service references environments)
SERVICE_ENVIRONMENT_RELATIONSHIP = EntityRelationship(
    source_entity="Service",
    target_entity="Environment",
    relation_type=RelationType.REFERENCE,
    attribute_name="environments",
    cascade_delete=False,
    required=False,
)


def get_plugin_relationships():
    """Get all entity relationships for this plugin.

    Returns:
        List of EntityRelationship objects
    """
    return [
        SERVICE_CONFIGURATION_RELATIONSHIP,
        SERVICE_ENVIRONMENT_RELATIONSHIP,
    ]
