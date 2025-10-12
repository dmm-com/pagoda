"""
Hook Name Definitions and Mapping

This module defines the standard hook names and provides mapping between
legacy custom_view hook names and the new standardized hook names for
backward compatibility.
"""

from typing import Dict, List

# Mapping from custom_view hook names to standard hook names
# This ensures backward compatibility with existing custom_view implementations
HOOK_ALIASES: Dict[str, str] = {
    # Entry lifecycle hooks
    "before_create_entry_v2": "entry.before_create",
    "after_create_entry_v2": "entry.after_create",
    "before_update_entry_v2": "entry.before_update",
    "after_update_entry_v2": "entry.after_update",
    "before_delete_entry_v2": "entry.before_delete",
    "before_restore_entry_v2": "entry.before_restore",
    "after_restore_entry_v2": "entry.after_restore",
    # Entity lifecycle hooks
    "before_create_entity_v2": "entity.before_create",
    "after_create_entity_v2": "entity.after_create",
    "before_update_entity_v2": "entity.before_update",
    "after_update_entity_v2": "entity.after_update",
    # Validation hooks
    "validate_entry": "entry.validate",
    # Data access hooks
    "get_entry_attr": "entry.get_attrs",
    "get_entity_attr": "entity.get_attrs",
}

# Reverse mapping (standard name → legacy name)
HOOK_ALIASES_REVERSE: Dict[str, str] = {v: k for k, v in HOOK_ALIASES.items()}

# All available standard hook names
AVAILABLE_HOOKS: List[str] = [
    # Entry lifecycle
    "entry.before_create",
    "entry.after_create",
    "entry.before_update",
    "entry.after_update",
    "entry.before_delete",
    "entry.before_restore",
    "entry.after_restore",
    # Entity lifecycle
    "entity.before_create",
    "entity.after_create",
    "entity.before_update",
    "entity.after_update",
    # Validation
    "entry.validate",
    # Data access
    "entry.get_attrs",
    "entity.get_attrs",
]

# Hook metadata for documentation and validation
HOOK_METADATA: Dict[str, Dict[str, str]] = {
    "entry.before_create": {
        "description": "Called before an entry is created",
        "args": "entity_name: str, user: User, validated_data: dict",
        "returns": "dict (modified validated_data) or None",
    },
    "entry.after_create": {
        "description": "Called after an entry is created",
        "args": "entity_name: str, user: User, entry: Entry",
        "returns": "None",
    },
    "entry.before_update": {
        "description": "Called before an entry is updated",
        "args": "entity_name: str, user: User, validated_data: dict, entry: Entry",
        "returns": "dict (modified validated_data) or None",
    },
    "entry.after_update": {
        "description": "Called after an entry is updated",
        "args": "entity_name: str, user: User, entry: Entry",
        "returns": "None",
    },
    "entry.before_delete": {
        "description": "Called before an entry is deleted",
        "args": "entity_name: str, user: User, entry: Entry",
        "returns": "None",
    },
    "entry.before_restore": {
        "description": "Called before an entry is restored",
        "args": "entity_name: str, user: User, entry: Entry",
        "returns": "None",
    },
    "entry.after_restore": {
        "description": "Called after an entry is restored",
        "args": "entity_name: str, user: User, entry: Entry",
        "returns": "None",
    },
    "entry.validate": {
        "description": "Custom validation for entry creation/update",
        "args": "user: User, schema_name: str, name: str, attrs: list, instance: Entry|None",
        "returns": "None (raises exception on validation error)",
    },
    "entry.get_attrs": {
        "description": "Modify entry attributes before returning to client",
        "args": "entry: Entry, attrinfo: list, is_retrieve: bool",
        "returns": "list (modified attrinfo)",
    },
    "entity.before_create": {
        "description": "Called before an entity is created",
        "args": "user: User, validated_data: dict",
        "returns": "dict (modified validated_data) or None",
    },
    "entity.after_create": {
        "description": "Called after an entity is created",
        "args": "user: User, entity: Entity",
        "returns": "None",
    },
    "entity.before_update": {
        "description": "Called before an entity is updated",
        "args": "user: User, validated_data: dict, entity: Entity",
        "returns": "dict (modified validated_data) or None",
    },
    "entity.after_update": {
        "description": "Called after an entity is updated",
        "args": "user: User, entity: Entity",
        "returns": "None",
    },
    "entity.get_attrs": {
        "description": "Modify entity attributes before returning to client",
        "args": "entity: Entity, attrinfo: list",
        "returns": "list (modified attrinfo)",
    },
}


def normalize_hook_name(handler_name: str) -> str:
    """Convert custom_view hook name to standard hook name

    Args:
        handler_name: Hook name (can be legacy custom_view name or standard name)

    Returns:
        Standardized hook name
    """
    # If already a standard name, return as-is
    if handler_name in AVAILABLE_HOOKS:
        return handler_name

    # Try to map from legacy name
    return HOOK_ALIASES.get(handler_name, handler_name)


def get_legacy_hook_name(hook_name: str) -> str:
    """Convert standard hook name to legacy custom_view name

    Args:
        hook_name: Standard hook name

    Returns:
        Legacy custom_view hook name, or the original name if no mapping exists
    """
    return HOOK_ALIASES_REVERSE.get(hook_name, hook_name)


def is_valid_hook_name(hook_name: str) -> bool:
    """Check if a hook name is valid (either standard or legacy)

    Args:
        hook_name: Hook name to validate

    Returns:
        True if the hook name is recognized
    """
    return hook_name in AVAILABLE_HOOKS or hook_name in HOOK_ALIASES


def get_hook_metadata(hook_name: str) -> Dict[str, str]:
    """Get metadata for a hook

    Args:
        hook_name: Hook name (standard or legacy)

    Returns:
        Dictionary containing hook metadata
    """
    standard_name = normalize_hook_name(hook_name)
    return HOOK_METADATA.get(standard_name, {})


def list_available_hooks() -> List[str]:
    """Get list of all available standard hook names

    Returns:
        List of standard hook names
    """
    return AVAILABLE_HOOKS.copy()


def list_legacy_hook_names() -> List[str]:
    """Get list of all legacy custom_view hook names

    Returns:
        List of legacy hook names
    """
    return list(HOOK_ALIASES.keys())
