"""
Decorators for plugin hook registration
"""

from functools import wraps
from typing import Any, Callable, Optional


def entry_hook(hook_type: str, entity: Optional[str] = None, priority: int = 100) -> Callable:
    """
    Decorator for entry lifecycle hooks.

    Args:
        hook_type: Hook type (e.g., "after_create", "before_update", "after_update")
        entity: Optional entity name to filter. If None, hook applies to all entities.
        priority: Execution priority (lower number = higher priority)

    Example:
        @entry_hook("after_create", entity="an")
        def log_create(self, user, entry, **kwargs):
            logger.info(f"Entry created: {entry.name}")
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)

        # Store hook metadata
        wrapper._hook_metadata = {  # type: ignore[attr-defined]
            "hook_name": f"entry.{hook_type}",
            "entity": entity,
            "priority": priority,
        }
        return wrapper

    return decorator


def entity_hook(hook_type: str, entity: Optional[str] = None, priority: int = 100) -> Callable:
    """
    Decorator for entity lifecycle hooks.

    Args:
        hook_type: Hook type (e.g., "after_create", "before_update")
        entity: Optional entity name to filter. If None, hook applies to all entities.
        priority: Execution priority (lower number = higher priority)

    Example:
        @entity_hook("after_create", entity="MyEntity")
        def log_entity_create(self, user, entity_obj, **kwargs):
            logger.info(f"Entity created: {entity_obj.name}")
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)

        # Store hook metadata
        wrapper._hook_metadata = {  # type: ignore[attr-defined]
            "hook_name": f"entity.{hook_type}",
            "entity": entity,
            "priority": priority,
        }
        return wrapper

    return decorator


def validation_hook(entity: Optional[str] = None, priority: int = 100) -> Callable:
    """
    Decorator for entry validation hooks.

    Args:
        entity: Optional entity name to filter. If None, hook applies to all entities.
        priority: Execution priority (lower number = higher priority)

    Example:
        @validation_hook(entity="an")
        def validate_an_entry(self, validated_data, entry, **kwargs):
            # Validation logic
            return validated_data
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)

        # Store hook metadata
        wrapper._hook_metadata = {  # type: ignore[attr-defined]
            "hook_name": "entry.validate",
            "entity": entity,
            "priority": priority,
        }
        return wrapper

    return decorator


def get_attrs_hook(hook_target: str, entity: Optional[str] = None, priority: int = 100) -> Callable:
    """
    Decorator for attribute retrieval hooks.

    Args:
        hook_target: Target type ("entry" or "entity")
        entity: Optional entity name to filter. If None, hook applies to all entities.
        priority: Execution priority (lower number = higher priority)

    Example:
        @get_attrs_hook("entry", entity="an")
        def get_entry_attrs(self, obj, **kwargs):
            # Return custom attributes
            return {"custom_field": "value"}
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)

        # Store hook metadata
        wrapper._hook_metadata = {  # type: ignore[attr-defined]
            "hook_name": f"{hook_target}.get_attrs",
            "entity": entity,
            "priority": priority,
        }
        return wrapper

    return decorator
