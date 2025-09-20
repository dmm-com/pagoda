"""
Interfaces for host application integration.

These interfaces define the contract between plugins and host applications.
Host applications must implement these interfaces to provide concrete functionality
to plugins, while plugins use these interfaces to access host application services.
"""

from .auth import AuthInterface
from .data import DataInterface
from .hooks import COMMON_HOOKS, HookInterface
from .models import (
    AttributeDict,
    AttributeProtocol,
    AttributeValueProtocol,
    EntityAttrProtocol,
    EntityDict,
    EntityProtocol,
    EntryDict,
    EntryProtocol,
    GroupProtocol,
    UserDict,
    UserProtocol,
    serialize_entity,
    serialize_entry,
    serialize_user,
    validate_entity_protocol,
    validate_entry_protocol,
    validate_user_protocol,
)

__all__ = [
    "AuthInterface",
    "DataInterface",
    "HookInterface",
    "COMMON_HOOKS",
    "EntityProtocol",
    "EntityAttrProtocol",
    "EntryProtocol",
    "AttributeProtocol",
    "AttributeValueProtocol",
    "UserProtocol",
    "GroupProtocol",
    "EntityDict",
    "EntryDict",
    "UserDict",
    "AttributeDict",
    "validate_entity_protocol",
    "validate_entry_protocol",
    "validate_user_protocol",
    "serialize_entity",
    "serialize_entry",
    "serialize_user",
]
