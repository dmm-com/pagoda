"""
Hook implementations for Hello World Plugin

Demonstrates how external plugins can extend Pagoda's core functionality through hooks.
"""

import logging
from datetime import datetime

# Import from Pagoda Core libraries (fully independent)
# Note: In production, plugins should use proper interface implementations

logger = logging.getLogger(__name__)


def after_entry_create(sender, instance, created, **kwargs):
    """Hook called after an entry is created

    Args:
        sender: Model class that sent the signal
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        # Basic logging (in production, plugins should use proper interface implementations)
        logger.info(
            f"Hello World Plugin: Entry created - {getattr(instance, 'name', 'unknown')} "
            f"(ID: {getattr(instance, 'id', None)}) "
            f"from model {sender.__name__ if sender else 'unknown'}"
        )


def before_entry_update(sender, instance, **kwargs):
    """Hook called before an entry is updated

    Args:
        sender: Model class that sent the signal
        instance: The actual instance being saved
        **kwargs: Additional keyword arguments
    """
    # Basic logging (in production, plugins should use proper interface implementations)
    logger.info(
        f"Hello World Plugin: Entry about to be updated - {getattr(instance, 'name', 'unknown')} "
        f"(ID: {getattr(instance, 'id', None)}) "
        f"from model {sender.__name__ if sender else 'unknown'}"
    )


def custom_processing_hook(data, context=None):
    """Custom processing hook

    Demonstrates how plugins can provide custom data processing.

    Args:
        data: Data to process
        context: Optional context information

    Returns:
        Processed data
    """
    # Basic logging (in production, plugins should use proper interface implementations)
    logger.info(
        f"Hello World Plugin: Custom processing - "
        f"data_type: {type(data).__name__}, context: {context}"
    )

    # Example processing: add plugin metadata
    if isinstance(data, dict):
        data["_plugin_processed_by"] = "hello-world-plugin"
        data["_processing_timestamp"] = str(datetime.now())
        data["_core"] = "pagoda-core"

    logger.info("Hello World Plugin: Custom processing completed")
    return data
