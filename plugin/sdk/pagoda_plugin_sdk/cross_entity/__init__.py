"""
Cross-entity operations module for pagoda-plugin-sdk.

This module provides utilities for plugins that need to perform operations
across multiple entities atomically.

Main Components:
    - EntityRelationship: Define relationships between entities
    - CompositeEntry: Represent main entry with related entries
    - CrossEntityOperation: Coordinate atomic operations across entities
    - BatchPermissionChecker: Efficiently check permissions for multiple entries
    - atomic_operation: Context manager for transactional operations
"""

from pagoda_plugin_sdk.cross_entity.composite import (
    CompletenessStatus,
    CompositeEntry,
    EntryNotAccessibleError,
    IncompleteCompositeError,
    ValidationResult,
)
from pagoda_plugin_sdk.cross_entity.logging import (
    CrossEntityLogEntry,
    CrossEntityLogger,
    log_cross_entity_operation,
)
from pagoda_plugin_sdk.cross_entity.operations import (
    CrossEntityOperation,
    OperationEntry,
    OperationResult,
    OperationStatus,
    OperationType,
)
from pagoda_plugin_sdk.cross_entity.permissions import (
    ACLType,
    BatchPermissionChecker,
    EntryPermission,
    PermissionCheckResult,
    PermissionDeniedError,
    check_permissions,
)
from pagoda_plugin_sdk.cross_entity.relationships import (
    CircularReferenceError,
    EntityRelationship,
    RelationshipRegistry,
    RelationType,
)
from pagoda_plugin_sdk.cross_entity.transaction import (
    AtomicOperationContext,
    OperationLog,
    TransactionError,
    atomic_operation,
)

__all__ = [
    # Relationships
    "EntityRelationship",
    "RelationType",
    "RelationshipRegistry",
    "CircularReferenceError",
    # Composite entries
    "CompositeEntry",
    "CompletenessStatus",
    "ValidationResult",
    "IncompleteCompositeError",
    "EntryNotAccessibleError",
    # Permissions
    "ACLType",
    "BatchPermissionChecker",
    "EntryPermission",
    "PermissionCheckResult",
    "PermissionDeniedError",
    "check_permissions",
    # Operations
    "CrossEntityOperation",
    "OperationType",
    "OperationStatus",
    "OperationEntry",
    "OperationResult",
    # Transactions
    "atomic_operation",
    "AtomicOperationContext",
    "OperationLog",
    "TransactionError",
    # Logging
    "CrossEntityLogEntry",
    "CrossEntityLogger",
    "log_cross_entity_operation",
]
