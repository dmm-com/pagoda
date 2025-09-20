"""
Data Access Interface.

This interface defines how plugins can interact with the host application's
data layer, including entities, entries, and other data objects.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class DataInterface(ABC):
    """Interface for data access services

    Host applications must implement this interface to provide data access
    services to plugins. This includes access to entities, entries, attributes,
    and other data objects.
    """

    @abstractmethod
    def get_entity(self, entity_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Get entity by ID

        Args:
            entity_id: Entity identifier

        Returns:
            Dictionary containing entity data or None if not found
        """
        pass

    @abstractmethod
    def get_entity_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get entity by name

        Args:
            name: Entity name

        Returns:
            Dictionary containing entity data or None if not found
        """
        pass

    @abstractmethod
    def get_entry(self, entry_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Get entry by ID

        Args:
            entry_id: Entry identifier

        Returns:
            Dictionary containing entry data or None if not found
        """
        pass

    @abstractmethod
    def get_entries(
        self,
        entity_id: Union[int, str],
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get entries for an entity

        Args:
            entity_id: Entity identifier
            filters: Optional filters to apply
            limit: Optional limit on number of results

        Returns:
            List of dictionaries containing entry data
        """
        pass

    @abstractmethod
    def create_entry(
        self, entity_id: Union[int, str], data: Dict[str, Any], user
    ) -> Dict[str, Any]:
        """Create a new entry

        Args:
            entity_id: Entity identifier
            data: Entry data
            user: User creating the entry

        Returns:
            Dictionary containing created entry data

        Raises:
            DataAccessError: If creation fails
        """
        pass

    @abstractmethod
    def update_entry(self, entry_id: Union[int, str], data: Dict[str, Any], user) -> Dict[str, Any]:
        """Update an existing entry

        Args:
            entry_id: Entry identifier
            data: Updated entry data
            user: User updating the entry

        Returns:
            Dictionary containing updated entry data

        Raises:
            DataAccessError: If update fails
        """
        pass

    @abstractmethod
    def delete_entry(self, entry_id: Union[int, str], user) -> bool:
        """Delete an entry

        Args:
            entry_id: Entry identifier
            user: User deleting the entry

        Returns:
            True if deletion successful, False otherwise

        Raises:
            DataAccessError: If deletion fails
        """
        pass

    @abstractmethod
    def search_entries(
        self,
        query: str,
        entity_ids: Optional[List[Union[int, str]]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search entries by query

        Args:
            query: Search query string
            entity_ids: Optional list of entity IDs to search within
            limit: Optional limit on number of results

        Returns:
            List of dictionaries containing matching entry data
        """
        pass

    def get_attribute_value(self, entry_id: Union[int, str], attribute_name: str) -> Any:
        """Get attribute value from an entry

        Args:
            entry_id: Entry identifier
            attribute_name: Name of the attribute

        Returns:
            Attribute value or None if not found

        Note:
            Default implementation returns None.
            Host applications should override this for attribute access.
        """
        return None

    def set_attribute_value(
        self, entry_id: Union[int, str], attribute_name: str, value: Any, user
    ) -> bool:
        """Set attribute value on an entry

        Args:
            entry_id: Entry identifier
            attribute_name: Name of the attribute
            value: Value to set
            user: User making the change

        Returns:
            True if successful, False otherwise

        Note:
            Default implementation returns False.
            Host applications should override this for attribute modification.
        """
        return False

    def get_entry_history(self, entry_id: Union[int, str]) -> List[Dict[str, Any]]:
        """Get entry modification history

        Args:
            entry_id: Entry identifier

        Returns:
            List of history records

        Note:
            Default implementation returns empty list.
            Host applications can override this for history access.
        """
        return []
