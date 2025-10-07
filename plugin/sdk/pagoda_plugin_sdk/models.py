"""
Model access for plugins.

This module provides access to host application models through a safe injection mechanism.
Models are injected by the host application during plugin system initialization.
"""

from typing import Optional, Type

from .protocols import (
    AttributeProtocol,
    AttributeValueProtocol,
    EntityAttrProtocol,
    EntityProtocol,
    EntryProtocol,
    UserProtocol,
)

# Model references - injected by the host application
Entity: Optional[Type[EntityProtocol]] = None
Entry: Optional[Type[EntryProtocol]] = None
User: Optional[Type[UserProtocol]] = None
AttributeValue: Optional[Type[AttributeValueProtocol]] = None
EntityAttr: Optional[Type[EntityAttrProtocol]] = None
Attribute: Optional[Type[AttributeProtocol]] = None


def __getattr__(name: str):
    """Handle access to model attributes with proper error messages"""

    # Map of available models
    available_models = {
        "Entity": Entity,
        "Entry": Entry,
        "User": User,
        "AttributeValue": AttributeValue,
        "EntityAttr": EntityAttr,
        "Attribute": Attribute,
    }

    if name in available_models:
        model = available_models[name]
        if model is None:
            raise ImportError(
                f"{name} model not available. "
                "Plugin system may not be initialized or model not registered. "
                "Make sure the host application has called plugin initialization."
            )
        return model

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def is_initialized() -> bool:
    """Check if models have been initialized

    Returns:
        True if at least one model has been injected, False otherwise
    """
    return any([Entity, Entry, User, AttributeValue, EntityAttr, Attribute])


def get_available_models() -> list[str]:
    """Get list of available (initialized) models

    Returns:
        List of model names that are currently available
    """
    available = []
    if Entity is not None:
        available.append("Entity")
    if Entry is not None:
        available.append("Entry")
    if User is not None:
        available.append("User")
    if AttributeValue is not None:
        available.append("AttributeValue")
    if EntityAttr is not None:
        available.append("EntityAttr")
    if Attribute is not None:
        available.append("Attribute")
    return available
