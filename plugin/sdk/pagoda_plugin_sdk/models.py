"""
Model access for plugins.

This module provides access to host application models through a safe injection mechanism.
Models are injected by the host application during plugin system initialization.
"""

from typing import List, Optional, Type

from .protocols import (
    AttributeProtocol,
    AttributeValueProtocol,
    EntityAttrProtocol,
    EntityProtocol,
    EntryProtocol,
    JobProtocol,
    UserProtocol,
)

# Model references - injected by the host application
Entity: Optional[Type[EntityProtocol]] = None
Entry: Optional[Type[EntryProtocol]] = None
User: Optional[Type[UserProtocol]] = None
AttributeValue: Optional[Type[AttributeValueProtocol]] = None
EntityAttr: Optional[Type[EntityAttrProtocol]] = None
Attribute: Optional[Type[AttributeProtocol]] = None
Job: Optional[Type[JobProtocol]] = None

# Cache for lazy-loaded components
_cache = {}

_EXPORTED_NAMES = [
    "PluginSchemaConfig",
]


def __getattr__(name: str):
    """Handle access to model attributes with proper error messages"""
    # return specified component component from _cache when it's existed
    if name in _cache:
        return _cache[name]

    if name in ("PluginSchemaConfig"):
        from airone.lib.plugin_model import PluginSchemaConfig

        _cache["PluginSchemaConfig"] = PluginSchemaConfig
        return _cache[name]

    # Map of available models
    available_models = {
        "Entity": Entity,
        "Entry": Entry,
        "User": User,
        "AttributeValue": AttributeValue,
        "EntityAttr": EntityAttr,
        "Attribute": Attribute,
        "Job": Job,
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


def __dir__():
    """Return list of available attributes for dir() and autocomplete"""
    return _EXPORTED_NAMES


def is_initialized() -> bool:
    """Check if models have been initialized

    Returns:
        True if at least one model has been injected, False otherwise
    """
    return any([Entity, Entry, User, AttributeValue, EntityAttr, Attribute, Job])


def get_available_models() -> List[str]:
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
    if Job is not None:
        available.append("Job")
    return available


class PluginSchema(object):
    def __init__(self, name=None, attrs={}, inheritance=None, exclude_attrs=[]):
        self.name = name
        self.attrs = attrs
        self.inheritance = inheritance
        self.exclude_attrs = exclude_attrs

    def get_attrs(self):
        returned_attrs = self.attrs
        if self.inheritance:
            inheritances = []
            if isinstance(self.inheritance, str):
                inheritances = [self.inheritance]
            elif isinstance(self.inheritance, list):
                inheritances = self.inheritance

            for ae_name_key in inheritances:
                inherited_adapted_entity = PluginSchema.get(ae_name_key)

                # This merges with inherited PluginSchema's attrs
                returned_attrs = dict(returned_attrs, **inherited_adapted_entity.get_attrs())

        # This excludes attrs which are explicitly set to exclude
        return {k: v for k, v in returned_attrs.items() if k not in self.exclude_attrs}

    def is_inherited(self, ae_name) -> bool:
        if isinstance(self.inheritance, str):
            return ae_name == self.inheritance
        elif isinstance(self.inheritance, list):
            return ae_name in self.inheritance

        return False

    def get_attr(self, name):
        return self.get_attrs()[name]

    def get_attrname(self, name):
        return self.get_attrs()[name]["name"]
