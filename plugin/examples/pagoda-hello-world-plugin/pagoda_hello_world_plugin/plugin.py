"""
Hello World Plugin for Pagoda

Demonstrates how to create external plugins using the Pagoda plugin system.
"""

import logging

# Import from Pagoda Plugin SDK libraries (fully independent)
from pagoda_plugin_sdk import Plugin
from pagoda_plugin_sdk.decorators import entity_hook, entry_hook, get_attrs_hook, validation_hook

# Use airone namespace logger to ensure logs are captured
logger = logging.getLogger("airone.plugins.hello_world")


class HelloWorldPlugin(Plugin):
    """Hello World Plugin

    A sample plugin that demonstrates:
    - Basic plugin structure
    - API endpoint registration
    - Hook system integration with decorators
    - Entity-specific hook filtering
    """

    # Plugin metadata
    id = "hello-world-plugin"
    name = "Hello World Plugin"
    version = "1.0.0"
    description = "A sample plugin demonstrating Pagoda plugin system capabilities"
    author = "Pagoda Development Team"

    # Django app configuration
    django_apps = ["pagoda_hello_world_plugin"]

    # API v2 endpoint configuration
    api_v2_patterns = "pagoda_hello_world_plugin.api_v2.urls"

    def __init__(self):
        """Initialize the Hello World plugin"""
        super().__init__()
        logger.info(f"Initialized {self.name} v{self.version}")

    # Entry Lifecycle Hooks - Entity-specific for 'helloworld'

    @entry_hook("after_create", entity="helloworld")
    def log_helloworld_create(self, entity_name, user, entry, **kwargs):
        """Called after an entry is created in 'helloworld' entity

        Args:
            entity_name: Name of the entity (will be 'helloworld')
            user: User who created the entry
            entry: The created Entry instance
            **kwargs: Additional context
        """
        logger.info(
            f"[Hello World Plugin] Entry created: '{entry.name}' "
            f"in entity '{entity_name}' by {user.username}"
        )

    @entry_hook("before_update", entity="helloworld")
    def log_helloworld_before_update(self, entity_name, user, validated_data, entry, **kwargs):
        """Called before an entry is updated in 'helloworld' entity

        Args:
            entity_name: Name of the entity (will be 'helloworld')
            user: User who is updating the entry
            validated_data: Dict of data that will be used for update
            entry: The Entry instance being updated
            **kwargs: Additional context

        Returns:
            Modified validated_data (or original)
        """
        logger.info(
            f"[Hello World Plugin] Entry updating: '{entry.name}' "
            f"in entity '{entity_name}' by {user.username}"
        )
        return validated_data

    @entry_hook("after_update", entity="helloworld")
    def log_helloworld_after_update(self, entity_name, user, entry, **kwargs):
        """Called after an entry is updated in 'helloworld' entity

        Args:
            entity_name: Name of the entity (will be 'helloworld')
            user: User who updated the entry
            entry: The updated Entry instance
            **kwargs: Additional context
        """
        logger.info(
            f"[Hello World Plugin] Entry updated: '{entry.name}' "
            f"in entity '{entity_name}' by {user.username}"
        )

    # Entry Lifecycle Hooks - Apply to all entities

    @entry_hook("before_delete")
    def log_entry_delete(self, entity_name, user, entry, **kwargs):
        """Called before an entry is deleted (all entities)

        Args:
            entity_name: Name of the entity
            user: User who is deleting the entry
            entry: The Entry instance being deleted
            **kwargs: Additional context
        """
        logger.info(
            f"[Hello World Plugin] Entry deleting: '{entry.name}' "
            f"in entity '{entity_name}' by {user.username}"
        )

    # Entry Validation Hook

    @validation_hook()
    def validate_entry(self, user, schema_name, name, attrs, instance, **kwargs):
        """Custom validation for entry creation/update

        Args:
            user: User creating/updating the entry
            schema_name: Name of the entity schema
            name: Entry name being validated
            attrs: List of attribute data
            instance: Existing Entry instance (None for creation)
            **kwargs: Additional context

        Raises:
            ValueError: If validation fails
        """
        logger.info(f"[Hello World Plugin] Validating entry: '{name}' in schema '{schema_name}'")

        # Example validation: Reject entries with "forbidden" in the name
        if "forbidden" in name.lower():
            raise ValueError("Entry name cannot contain 'forbidden' (plugin rule)")

    # Entry Data Access Hook

    @get_attrs_hook("entry")
    def get_entry_attrs(self, entry, attrinfo, is_retrieve, **kwargs):
        """Modify entry attributes before returning to client

        Args:
            entry: Entry instance
            attrinfo: List of attribute information dicts
            is_retrieve: Boolean indicating if this is a retrieve operation
            **kwargs: Additional context

        Returns:
            Modified attrinfo list
        """
        logger.info(
            f"[Hello World Plugin] Getting entry attrs for: '{entry.name}' "
            f"(retrieve: {is_retrieve})"
        )
        return attrinfo

    # Entity Lifecycle Hooks

    @entity_hook("after_create")
    def log_entity_create(self, user, entity, **kwargs):
        """Called after an entity is created

        Args:
            user: User who created the entity
            entity: The created Entity instance
            **kwargs: Additional context
        """
        logger.info(f"[Hello World Plugin] Entity created: '{entity.name}' by {user.username}")

    @entity_hook("before_update")
    def log_entity_before_update(self, user, validated_data, entity, **kwargs):
        """Called before an entity is updated

        Args:
            user: User who is updating the entity
            validated_data: Dict of data that will be used for update
            entity: The Entity instance being updated
            **kwargs: Additional context

        Returns:
            Modified validated_data (or original)
        """
        logger.info(f"[Hello World Plugin] Entity updating: '{entity.name}' by {user.username}")
        return validated_data

    @entity_hook("after_update")
    def log_entity_after_update(self, user, entity, **kwargs):
        """Called after an entity is updated

        Args:
            user: User who updated the entity
            entity: The updated Entity instance
            **kwargs: Additional context
        """
        logger.info(f"[Hello World Plugin] Entity updated: '{entity.name}' by {user.username}")

    # Entity Data Access Hook

    @get_attrs_hook("entity")
    def get_entity_attrs(self, entity, attrinfo, **kwargs):
        """Modify entity attributes before returning to client

        Args:
            entity: Entity instance
            attrinfo: List of entity attribute information dicts
            **kwargs: Additional context

        Returns:
            Modified attrinfo list
        """
        logger.info(f"[Hello World Plugin] Getting entity attrs for: '{entity.name}'")
        return attrinfo
