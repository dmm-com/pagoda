"""
AirOne Utility Functions for Plugins

Provides utility functions that plugins can use to interact with AirOne core functionality.
"""

import logging
from typing import Any, Dict, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def get_airone_version() -> str:
    """Get AirOne version

    Returns:
        AirOne version string
    """
    # This would typically come from a version file or package metadata
    return "1.0.0"  # Placeholder


def get_airone_settings(key: Optional[str] = None, default: Any = None) -> Any:
    """Get AirOne configuration settings

    Provides safe access to AirOne settings for plugins.

    Args:
        key: Setting key to retrieve. If None, returns all available settings.
        default: Default value if key is not found

    Returns:
        Setting value or default
    """
    if key is None:
        # Return subset of settings that plugins are allowed to access
        return {
            "ENABLED_PLUGINS": getattr(settings, "ENABLED_PLUGINS", []),
            "DEBUG": getattr(settings, "DEBUG", False),
            "VERSION": get_airone_version(),
        }

    # Allowed settings for plugins
    allowed_settings = [
        "ENABLED_PLUGINS",
        "DEBUG",
        "TIME_ZONE",
        "LANGUAGE_CODE",
    ]

    if key not in allowed_settings:
        logger.warning(f"Plugin attempted to access restricted setting: {key}")
        return default

    return getattr(settings, key, default)


def log_plugin_activity(plugin_id: str, action: str, details: Optional[Dict[str, Any]] = None):
    """Log plugin activity

    Provides centralized logging for plugin activities.

    Args:
        plugin_id: Plugin identifier
        action: Action being performed
        details: Additional details about the action
    """
    log_entry = f"Plugin '{plugin_id}' performed action: {action}"
    if details:
        log_entry += f" | Details: {details}"

    logger.info(log_entry)


def validate_plugin_data(data: Dict[str, Any], required_fields: list) -> Dict[str, Any]:
    """Validate plugin data

    Validates that required fields are present in plugin data.

    Args:
        data: Data to validate
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
    }


def format_datetime_for_api(dt) -> Optional[str]:
    """Format datetime for API response

    Args:
        dt: DateTime object to format

    Returns:
        ISO formatted datetime string or None
    """
    if dt is None:
        return None

    return dt.isoformat()


def get_plugin_cache_key(plugin_id: str, key: str) -> str:
    """Generate cache key for plugin data

    Args:
        plugin_id: Plugin identifier
        key: Cache key

    Returns:
        Formatted cache key
    """
    return f"plugin:{plugin_id}:{key}"
