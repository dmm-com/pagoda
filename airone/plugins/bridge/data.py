"""
AirOne Data Access Bridge

Implements pagoda_core.interfaces.DataInterface with AirOne-specific logic.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from pagoda_core.interfaces import DataInterface
from pagoda_core.exceptions import DataAccessError

logger = logging.getLogger(__name__)


class AirOneDataBridge(DataInterface):
    """AirOne-specific implementation of DataInterface

    This bridge connects pagoda-core's data access interface to AirOne's
    data models (entities, entries, attributes), providing plugins with
    access to AirOne's data layer.
    """

    def get_entity(self, entity_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Get entity by ID from AirOne

        Args:
            entity_id: Entity identifier

        Returns:
            Dictionary containing entity data or None if not found
        """
        try:
            from entity.models import Entity

            entity = Entity.objects.filter(id=entity_id, is_active=True).first()
            if not entity:
                return None

            return {
                "id": entity.id,
                "name": entity.name,
                "note": getattr(entity, 'note', ''),
                "is_active": entity.is_active,
                "created_user": entity.created_user.username if entity.created_user else None,
                "created_time": entity.created_time.isoformat() if entity.created_time else None,
            }
        except ImportError:
            logger.error("Entity model not available")
            return None
        except Exception as e:
            logger.error(f"Error getting entity {entity_id}: {e}")
            return None

    def get_entity_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get entity by name from AirOne

        Args:
            name: Entity name

        Returns:
            Dictionary containing entity data or None if not found
        """
        try:
            from entity.models import Entity

            entity = Entity.objects.filter(name=name, is_active=True).first()
            if not entity:
                return None

            return {
                "id": entity.id,
                "name": entity.name,
                "note": getattr(entity, 'note', ''),
                "is_active": entity.is_active,
                "created_user": entity.created_user.username if entity.created_user else None,
                "created_time": entity.created_time.isoformat() if entity.created_time else None,
            }
        except ImportError:
            logger.error("Entity model not available")
            return None
        except Exception as e:
            logger.error(f"Error getting entity by name '{name}': {e}")
            return None

    def get_entry(self, entry_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Get entry by ID from AirOne

        Args:
            entry_id: Entry identifier

        Returns:
            Dictionary containing entry data or None if not found
        """
        try:
            from entry.models import Entry

            entry = Entry.objects.filter(id=entry_id, is_active=True).first()
            if not entry:
                return None

            return {
                "id": entry.id,
                "name": entry.name,
                "entity": {
                    "id": entry.schema.id,
                    "name": entry.schema.name,
                } if entry.schema else None,
                "is_active": entry.is_active,
                "created_user": entry.created_user.username if entry.created_user else None,
                "created_time": entry.created_time.isoformat() if entry.created_time else None,
            }
        except ImportError:
            logger.error("Entry model not available")
            return None
        except Exception as e:
            logger.error(f"Error getting entry {entry_id}: {e}")
            return None

    def get_entries(self, entity_id: Union[int, str],
                   filters: Optional[Dict[str, Any]] = None,
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get entries for an entity from AirOne

        Args:
            entity_id: Entity identifier
            filters: Optional filters to apply
            limit: Optional limit on number of results

        Returns:
            List of dictionaries containing entry data
        """
        try:
            from entry.models import Entry
            from entity.models import Entity

            entity = Entity.objects.filter(id=entity_id, is_active=True).first()
            if not entity:
                return []

            queryset = Entry.objects.filter(schema=entity, is_active=True)

            if filters:
                # Apply basic filters
                if 'name' in filters:
                    queryset = queryset.filter(name__icontains=filters['name'])

            if limit:
                queryset = queryset[:limit]

            entries = []
            for entry in queryset:
                entries.append({
                    "id": entry.id,
                    "name": entry.name,
                    "entity": {
                        "id": entity.id,
                        "name": entity.name,
                    },
                    "is_active": entry.is_active,
                    "created_user": entry.created_user.username if entry.created_user else None,
                    "created_time": entry.created_time.isoformat() if entry.created_time else None,
                })

            return entries
        except ImportError:
            logger.error("Entry/Entity models not available")
            return []
        except Exception as e:
            logger.error(f"Error getting entries for entity {entity_id}: {e}")
            return []

    def create_entry(self, entity_id: Union[int, str],
                    data: Dict[str, Any], user) -> Dict[str, Any]:
        """Create a new entry in AirOne

        Args:
            entity_id: Entity identifier
            data: Entry data
            user: User creating the entry

        Returns:
            Dictionary containing created entry data

        Raises:
            DataAccessError: If creation fails
        """
        try:
            from entry.models import Entry
            from entity.models import Entity

            entity = Entity.objects.filter(id=entity_id, is_active=True).first()
            if not entity:
                raise DataAccessError(f"Entity {entity_id} not found or inactive")

            if 'name' not in data:
                raise DataAccessError("Entry name is required")

            entry = Entry.objects.create(
                name=data['name'],
                schema=entity,
                created_user=user,
            )

            return {
                "id": entry.id,
                "name": entry.name,
                "entity": {
                    "id": entity.id,
                    "name": entity.name,
                },
                "is_active": entry.is_active,
                "created_user": entry.created_user.username if entry.created_user else None,
                "created_time": entry.created_time.isoformat() if entry.created_time else None,
            }
        except ImportError:
            logger.error("Entry/Entity models not available")
            raise DataAccessError("Entry/Entity models not available")
        except Exception as e:
            logger.error(f"Error creating entry: {e}")
            raise DataAccessError(f"Failed to create entry: {e}")

    def update_entry(self, entry_id: Union[int, str],
                    data: Dict[str, Any], user) -> Dict[str, Any]:
        """Update an existing entry in AirOne

        Args:
            entry_id: Entry identifier
            data: Updated entry data
            user: User updating the entry

        Returns:
            Dictionary containing updated entry data

        Raises:
            DataAccessError: If update fails
        """
        try:
            from entry.models import Entry

            entry = Entry.objects.filter(id=entry_id, is_active=True).first()
            if not entry:
                raise DataAccessError(f"Entry {entry_id} not found or inactive")

            if 'name' in data:
                entry.name = data['name']

            entry.save()

            return {
                "id": entry.id,
                "name": entry.name,
                "entity": {
                    "id": entry.schema.id,
                    "name": entry.schema.name,
                } if entry.schema else None,
                "is_active": entry.is_active,
                "created_user": entry.created_user.username if entry.created_user else None,
                "created_time": entry.created_time.isoformat() if entry.created_time else None,
            }
        except ImportError:
            logger.error("Entry model not available")
            raise DataAccessError("Entry model not available")
        except Exception as e:
            logger.error(f"Error updating entry: {e}")
            raise DataAccessError(f"Failed to update entry: {e}")

    def delete_entry(self, entry_id: Union[int, str], user) -> bool:
        """Delete an entry in AirOne (soft delete)

        Args:
            entry_id: Entry identifier
            user: User deleting the entry

        Returns:
            True if deletion successful, False otherwise

        Raises:
            DataAccessError: If deletion fails
        """
        try:
            from entry.models import Entry

            entry = Entry.objects.filter(id=entry_id, is_active=True).first()
            if not entry:
                return False

            # Soft delete by setting is_active to False
            entry.is_active = False
            entry.save()

            return True
        except ImportError:
            logger.error("Entry model not available")
            raise DataAccessError("Entry model not available")
        except Exception as e:
            logger.error(f"Error deleting entry: {e}")
            raise DataAccessError(f"Failed to delete entry: {e}")

    def search_entries(self, query: str,
                      entity_ids: Optional[List[Union[int, str]]] = None,
                      limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search entries by query in AirOne

        Args:
            query: Search query string
            entity_ids: Optional list of entity IDs to search within
            limit: Optional limit on number of results

        Returns:
            List of dictionaries containing matching entry data
        """
        try:
            from entry.models import Entry
            from entity.models import Entity

            queryset = Entry.objects.filter(is_active=True)

            if query:
                queryset = queryset.filter(name__icontains=query)

            if entity_ids:
                queryset = queryset.filter(schema_id__in=entity_ids)

            if limit:
                queryset = queryset[:limit]

            entries = []
            for entry in queryset:
                entries.append({
                    "id": entry.id,
                    "name": entry.name,
                    "entity": {
                        "id": entry.schema.id,
                        "name": entry.schema.name,
                    } if entry.schema else None,
                    "is_active": entry.is_active,
                    "created_user": entry.created_user.username if entry.created_user else None,
                    "created_time": entry.created_time.isoformat() if entry.created_time else None,
                })

            return entries
        except ImportError:
            logger.error("Entry model not available")
            return []
        except Exception as e:
            logger.error(f"Error searching entries: {e}")
            return []