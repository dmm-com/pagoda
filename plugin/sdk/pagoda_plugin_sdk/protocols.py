"""
Protocol definitions for Pagoda models.

These protocols define the interface for accessing host application models
in a type-safe manner without creating implementation dependencies.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Protocol, runtime_checkable


class EntityManagerProtocol(Protocol):
    """Protocol for Entity model manager"""

    def filter(self, **kwargs) -> Any: ...
    def get(self, **kwargs) -> "EntityProtocol": ...
    def create(self, **kwargs) -> "EntityProtocol": ...
    def all(self) -> Any: ...
    def count(self) -> int: ...


@runtime_checkable
class EntityProtocol(Protocol):
    """Protocol for Entity model"""

    # Fields
    id: int
    name: str
    note: str
    is_active: bool
    created_time: Optional[datetime]
    created_user: Any

    # Manager
    objects: EntityManagerProtocol

    # Methods
    def save(self, **kwargs) -> None: ...
    def delete(self) -> None: ...
    def __str__(self) -> str: ...


class EntryManagerProtocol(Protocol):
    """Protocol for Entry model manager"""

    def filter(self, **kwargs) -> Any: ...
    def get(self, **kwargs) -> "EntryProtocol": ...
    def create(self, **kwargs) -> "EntryProtocol": ...
    def all(self) -> Any: ...
    def count(self) -> int: ...


@runtime_checkable
class EntryProtocol(Protocol):
    """Protocol for Entry model"""

    # Fields
    id: int
    name: str
    note: str
    is_active: bool
    schema: EntityProtocol
    created_time: Optional[datetime]
    created_user: Any
    updated_time: Optional[datetime]

    # Manager
    objects: EntryManagerProtocol

    # Methods
    def save(self, **kwargs) -> None: ...
    def delete(self) -> None: ...
    def get_attrs(self, **kwargs) -> Dict[str, Any]: ...
    def set_attrs(self, user: Any, **kwargs) -> None: ...
    def may_permitted(self, user: Any, permission: Any) -> bool: ...
    def __str__(self) -> str: ...


class EntityAttrManagerProtocol(Protocol):
    """Protocol for EntityAttr model manager"""

    def filter(self, **kwargs) -> Any: ...
    def get(self, **kwargs) -> "EntityAttrProtocol": ...
    def create(self, **kwargs) -> "EntityAttrProtocol": ...
    def all(self) -> Any: ...
    def count(self) -> int: ...


class EntityAttrProtocol(Protocol):
    """Protocol for EntityAttr model"""

    # Fields
    id: int
    name: str
    type: int
    is_mandatory: bool
    referral: Any
    index: int
    is_summarized: bool
    is_delete_in_chain: bool
    note: str
    default_value: Any
    parent_entity: EntityProtocol
    is_active: bool
    created_time: Optional[datetime]
    created_user: Any

    # Manager
    objects: EntityAttrManagerProtocol

    # Methods
    def save(self, **kwargs) -> None: ...
    def delete(self) -> None: ...
    def is_updated(
        self,
        name: str,
        is_mandatory: bool,
        is_delete_in_chain: bool,
        index: int,
        default_value: Any,
    ) -> bool: ...
    def is_referral_updated(self, refs: Any) -> bool: ...
    def referral_clear(self) -> None: ...
    def add_referral(self, referral: Any) -> None: ...
    def get_default_value(self) -> Any: ...
    def __str__(self) -> str: ...


class AttributeManagerProtocol(Protocol):
    """Protocol for Attribute model manager"""

    def filter(self, **kwargs) -> Any: ...
    def get(self, **kwargs) -> "AttributeProtocol": ...
    def create(self, **kwargs) -> "AttributeProtocol": ...
    def all(self) -> Any: ...
    def count(self) -> int: ...


class AttributeProtocol(Protocol):
    """Protocol for Attribute model"""

    # Fields
    id: int
    name: str
    values: Any
    schema: EntityAttrProtocol
    parent_entry: EntryProtocol
    is_active: bool
    created_time: Optional[datetime]
    created_user: Any

    # Manager
    objects: AttributeManagerProtocol

    # Methods
    def save(self, **kwargs) -> None: ...
    def delete(self) -> None: ...
    def is_array(self) -> bool: ...
    def is_updated(self, recv_value: Any) -> bool: ...
    def __str__(self) -> str: ...


@runtime_checkable
class UserProtocol(Protocol):
    """Protocol for User model"""

    # Fields
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_superuser: bool
    date_joined: Optional[datetime]

    # Methods
    def __str__(self) -> str: ...


class AttributeValueProtocol(Protocol):
    """Protocol for AttributeValue model"""

    # Fields
    id: int
    parent_entry: EntryProtocol
    is_active: bool
    created_time: Optional[datetime]
    created_user: Any

    # Methods
    def save(self, **kwargs) -> None: ...
    def delete(self) -> None: ...
    def __str__(self) -> str: ...


class JobProtocol(Protocol):
    # Fields
    user: UserProtocol
    created_at: datetime
    updated_at: datetime
    target: EntryProtocol
    target_type: int
    status: int
    operation: int
    text: str
    params: str

    # NOTE: I don't know how to specify dependent_job that refers this class recursively
    #    dependent_job: Optional[JobProtocol]

    # Methods
    def may_schedule(self) -> bool: ...
    def is_timeout(self) -> bool: ...
    def is_finished(self, with_refresh: bool = True) -> bool: ...
    def is_canceled(self) -> bool: ...
    def proceed_if_ready(self) -> bool: ...
    def update(
        self,
        status,
        text,
        target,
        operation,
    ): ...
    def to_json(self) -> dict: ...
    def run(self, will_delay=True): ...
    def method_table(kls) -> dict: ...
    def register_method_table(kls, operation, method): ...
