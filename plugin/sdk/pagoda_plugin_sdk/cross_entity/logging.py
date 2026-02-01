"""
Logging utilities for cross-entity operations.

This module provides structured logging helpers for auditing and debugging
cross-entity operations.
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from pagoda_plugin_sdk.protocols import UserProtocol

logger = logging.getLogger(__name__)


@dataclass
class CrossEntityLogEntry:
    """Structured log entry for cross-entity operations."""

    plugin_id: str
    user_id: int
    username: str
    operation: str
    affected_entries: int
    entities: List[str]
    status: str
    timestamp: str
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class CrossEntityLogger:
    """Logger for cross-entity operations.

    Provides structured logging for auditing cross-entity operations,
    including user context, affected entries, and operation status.

    Usage:
        log = CrossEntityLogger("my-plugin", user)
        log.log_operation(
            operation="create_composite",
            affected_entries=5,
            entities=["Service", "Configuration"],
            status="success",
        )
    """

    def __init__(
        self,
        plugin_id: str,
        user: Optional["UserProtocol"] = None,
        logger_name: Optional[str] = None,
    ):
        """Initialize the logger.

        Args:
            plugin_id: ID of the plugin
            user: User performing the operation
            logger_name: Custom logger name (defaults to module logger)
        """
        self.plugin_id = plugin_id
        self.user = user
        self._logger = logging.getLogger(logger_name) if logger_name else logger

    def log_operation(
        self,
        operation: str,
        affected_entries: int,
        entities: List[str],
        status: str,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> CrossEntityLogEntry:
        """Log a cross-entity operation.

        Args:
            operation: Type of operation (e.g., "create_composite", "update", "delete")
            affected_entries: Number of entries affected
            entities: List of entity names involved
            status: Operation status ("success", "failed", "partial")
            duration_ms: Operation duration in milliseconds
            error: Error message if operation failed
            details: Additional operation details

        Returns:
            CrossEntityLogEntry for the logged operation
        """
        user_id = 0
        username = "unknown"
        if self.user:
            if hasattr(self.user, "id"):
                user_id = self.user.id
            if hasattr(self.user, "username"):
                username = self.user.username

        entry = CrossEntityLogEntry(
            plugin_id=self.plugin_id,
            user_id=user_id,
            username=username,
            operation=operation,
            affected_entries=affected_entries,
            entities=entities,
            status=status,
            timestamp=datetime.now().isoformat(),
            duration_ms=duration_ms,
            error=error,
            details=details,
        )

        log_message = f"Cross-entity operation: {entry.to_dict()}"

        if status == "failed":
            self._logger.error(log_message)
        elif status == "partial":
            self._logger.warning(log_message)
        else:
            self._logger.info(log_message)

        return entry

    def log_permission_check(
        self,
        entries_checked: int,
        entries_denied: int,
        entities: List[str],
    ) -> None:
        """Log a permission check operation.

        Args:
            entries_checked: Number of entries checked
            entries_denied: Number of entries denied
            entities: List of entity names involved
        """
        status = "granted" if entries_denied == 0 else "denied"
        self.log_operation(
            operation="permission_check",
            affected_entries=entries_checked,
            entities=entities,
            status=status,
            details={
                "checked": entries_checked,
                "denied": entries_denied,
            },
        )

    def log_transaction(
        self,
        created: int,
        updated: int,
        deleted: int,
        entities: List[str],
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log a transaction summary.

        Args:
            created: Number of entries created
            updated: Number of entries updated
            deleted: Number of entries deleted
            entities: List of entity names involved
            success: Whether the transaction succeeded
            error: Error message if transaction failed
        """
        self.log_operation(
            operation="transaction",
            affected_entries=created + updated + deleted,
            entities=entities,
            status="success" if success else "failed",
            error=error,
            details={
                "created": created,
                "updated": updated,
                "deleted": deleted,
            },
        )


def log_cross_entity_operation(
    plugin_id: str,
    user: Optional["UserProtocol"],
    operation: str,
    affected_entries: int,
    entities: List[str],
    status: str,
    duration_ms: Optional[int] = None,
    error: Optional[str] = None,
) -> CrossEntityLogEntry:
    """Convenience function for logging cross-entity operations.

    Args:
        plugin_id: ID of the plugin
        user: User performing the operation
        operation: Type of operation
        affected_entries: Number of entries affected
        entities: List of entity names
        status: Operation status
        duration_ms: Operation duration in milliseconds
        error: Error message if failed

    Returns:
        CrossEntityLogEntry for the logged operation
    """
    cross_logger = CrossEntityLogger(plugin_id, user)
    return cross_logger.log_operation(
        operation=operation,
        affected_entries=affected_entries,
        entities=entities,
        status=status,
        duration_ms=duration_ms,
        error=error,
    )
