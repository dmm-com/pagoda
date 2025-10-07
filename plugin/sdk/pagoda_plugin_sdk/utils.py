"""
Utility functions for plugin development.

These utilities provide common functionality that plugins might need,
such as version information, logging helpers, and validation functions.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def get_pagoda_version() -> str:
    """Get Pagoda Core version

    Returns:
        Version string
    """
    from . import __version__

    return __version__


def validate_plugin_data(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """Validate plugin data structure

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names

    Returns:
        Dictionary with validation results

    Raises:
        ValueError: If validation fails
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)

    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    return {
        "valid": True,
        "data": data,
        "validated_fields": required_fields,
    }


def format_datetime_for_api(dt: Any) -> Optional[str]:
    """Format datetime for API response

    Args:
        dt: DateTime object to format

    Returns:
        ISO formatted datetime string or None
    """
    if dt is None:
        return None

    try:
        return str(dt.isoformat())
    except AttributeError:
        # If dt is not a datetime object, try to convert it to string
        return str(dt)


def sanitize_plugin_id(plugin_id: str) -> str:
    """Sanitize plugin ID for safe usage

    Args:
        plugin_id: Plugin ID to sanitize

    Returns:
        Sanitized plugin ID
    """
    if not plugin_id:
        return ""

    # Keep only alphanumeric characters, hyphens, and underscores
    sanitized = "".join(c for c in plugin_id if c.isalnum() or c in "-_")

    # Remove leading/trailing hyphens and underscores
    sanitized = sanitized.strip("-_")

    return sanitized


def generate_plugin_cache_key(plugin_id: str, key: str) -> str:
    """Generate cache key for plugin data

    Args:
        plugin_id: Plugin identifier
        key: Cache key

    Returns:
        Formatted cache key
    """
    sanitized_id = sanitize_plugin_id(plugin_id)
    return f"pagoda:plugin:{sanitized_id}:{key}"


def log_plugin_activity(plugin_id: str, action: str, details: Optional[Dict[str, Any]] = None):
    """Log plugin activity

    Args:
        plugin_id: Plugin identifier
        action: Action being performed
        details: Optional additional details
    """
    log_message = f"Plugin '{plugin_id}' performed action: {action}"
    if details:
        log_message += f" | Details: {details}"

    logger.info(log_message)


def merge_plugin_config(
    default_config: Dict[str, Any], plugin_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge plugin configuration with defaults

    Args:
        default_config: Default configuration values
        plugin_config: Plugin-specific configuration

    Returns:
        Merged configuration dictionary
    """
    merged = default_config.copy()
    merged.update(plugin_config)
    return merged


def validate_django_app_name(app_name: str) -> bool:
    """Validate Django app name format

    Args:
        app_name: Django app name to validate

    Returns:
        True if valid, False otherwise
    """
    if not app_name or not isinstance(app_name, str):
        return False

    # Django app names should be valid Python identifiers
    # but can also contain dots for package paths
    parts = app_name.split(".")
    return all(part.isidentifier() for part in parts)


def get_plugin_module_path(plugin_id: str, module_name: str) -> str:
    """Generate module path for plugin

    Args:
        plugin_id: Plugin identifier
        module_name: Module name within plugin

    Returns:
        Full module path
    """
    # Convert plugin ID to valid Python module name
    module_id = plugin_id.replace("-", "_")
    return f"{module_id}.{module_name}"


class PluginLogger:
    """Specialized logger for plugins"""

    def __init__(self, plugin_id: str):
        self.plugin_id = plugin_id
        self.logger = logging.getLogger(f"pagoda.plugin.{plugin_id}")

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(f"[{self.plugin_id}] {message}", **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(f"[{self.plugin_id}] {message}", **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(f"[{self.plugin_id}] {message}", **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(f"[{self.plugin_id}] {message}", **kwargs)
