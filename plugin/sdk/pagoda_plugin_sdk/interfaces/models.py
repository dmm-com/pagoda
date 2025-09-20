"""
Model interfaces and protocols for pagoda-core.

These protocols define the minimum requirements for data models that
plugins can expect from host applications. They provide type safety
and documentation without creating hard dependencies on specific
model implementations.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class EntityProtocol(Protocol):
    """Protocol for Entity-like objects

    Defines the minimum interface that entity objects must implement
    to be compatible with pagoda-core plugins.
    """

    id: int
    name: str
    note: str
    is_active: bool
    created_time: Optional[datetime]
    created_user: Optional["UserProtocol"]

    def __str__(self) -> str:
        """String representation of the entity"""
        ...


@runtime_checkable
class EntityAttrProtocol(Protocol):
    """Protocol for EntityAttr-like objects

    Defines the minimum interface for entity attribute definitions.
    """

    id: int
    name: str
    type: int
    is_mandatory: bool
    is_delete_in_chain: bool
    is_summarized: bool
    note: str
    index: int
    default_value: Optional[Any]
    parent_entity: EntityProtocol

    def __str__(self) -> str:
        """String representation of the entity attribute"""
        ...


@runtime_checkable
class EntryProtocol(Protocol):
    """Protocol for Entry-like objects

    Defines the minimum interface that entry objects must implement
    to be compatible with pagoda-core plugins.
    """

    id: int
    name: str
    note: str
    is_active: bool
    schema: EntityProtocol
    created_time: Optional[datetime]
    created_user: Optional["UserProtocol"]
    updated_time: Optional[datetime]

    def __str__(self) -> str:
        """String representation of the entry"""
        ...


@runtime_checkable
class AttributeProtocol(Protocol):
    """Protocol for Attribute-like objects

    Defines the minimum interface for entry attributes.
    """

    id: int
    name: str
    is_active: bool
    schema: EntityAttrProtocol
    parent_entry: EntryProtocol
    created_time: Optional[datetime]
    created_user: Optional["UserProtocol"]

    def __str__(self) -> str:
        """String representation of the attribute"""
        ...


@runtime_checkable
class AttributeValueProtocol(Protocol):
    """Protocol for AttributeValue-like objects

    Defines the minimum interface for attribute values.
    """

    id: int
    value: str
    boolean: bool
    referral: Optional["EntryProtocol"]
    created_time: Optional[datetime]
    created_user: Optional["UserProtocol"]
    parent_attr: AttributeProtocol

    def __str__(self) -> str:
        """String representation of the attribute value"""
        ...


@runtime_checkable
class UserProtocol(Protocol):
    """Protocol for User-like objects

    Defines the minimum interface that user objects must implement
    to be compatible with pagoda-core plugins.
    """

    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_superuser: bool
    date_joined: Optional[datetime]

    def __str__(self) -> str:
        """String representation of the user"""
        ...


@runtime_checkable
class GroupProtocol(Protocol):
    """Protocol for Group-like objects

    Defines the minimum interface for group objects.
    """

    id: int
    name: str
    is_active: bool

    def __str__(self) -> str:
        """String representation of the group"""
        ...


# Type aliases for convenience
EntityDict = Dict[str, Any]
EntryDict = Dict[str, Any]
UserDict = Dict[str, Any]
AttributeDict = Dict[str, Any]


def validate_entity_protocol(obj: Any) -> bool:
    """Validate if an object conforms to EntityProtocol

    Args:
        obj: Object to validate

    Returns:
        True if object conforms to EntityProtocol
    """
    try:
        return isinstance(obj, EntityProtocol)
    except (AttributeError, TypeError):
        return False


def validate_entry_protocol(obj: Any) -> bool:
    """Validate if an object conforms to EntryProtocol

    Args:
        obj: Object to validate

    Returns:
        True if object conforms to EntryProtocol
    """
    try:
        return isinstance(obj, EntryProtocol)
    except (AttributeError, TypeError):
        return False


def validate_user_protocol(obj: Any) -> bool:
    """Validate if an object conforms to UserProtocol

    Args:
        obj: Object to validate

    Returns:
        True if object conforms to UserProtocol
    """
    try:
        return isinstance(obj, UserProtocol)
    except (AttributeError, TypeError):
        return False


def serialize_entity(entity: EntityProtocol) -> EntityDict:
    """Serialize an entity object to dictionary

    Args:
        entity: Entity object conforming to EntityProtocol

    Returns:
        Dictionary representation of the entity
    """
    return {
        "id": entity.id,
        "name": entity.name,
        "note": entity.note,
        "is_active": entity.is_active,
        "created_time": entity.created_time.isoformat() if entity.created_time else None,
        "created_user": entity.created_user.username if entity.created_user else None,
    }


def serialize_entry(entry: EntryProtocol) -> EntryDict:
    """Serialize an entry object to dictionary

    Args:
        entry: Entry object conforming to EntryProtocol

    Returns:
        Dictionary representation of the entry
    """
    return {
        "id": entry.id,
        "name": entry.name,
        "note": entry.note,
        "is_active": entry.is_active,
        "schema": serialize_entity(entry.schema),
        "created_time": entry.created_time.isoformat() if entry.created_time else None,
        "created_user": entry.created_user.username if entry.created_user else None,
        "updated_time": entry.updated_time.isoformat() if entry.updated_time else None,
    }


def serialize_user(user: UserProtocol) -> UserDict:
    """Serialize a user object to dictionary

    Args:
        user: User object conforming to UserProtocol

    Returns:
        Dictionary representation of the user
    """
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "date_joined": user.date_joined.isoformat() if user.date_joined else None,
    }
