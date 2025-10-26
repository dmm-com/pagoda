"""
Plugin Task Management System

This module provides safe and flexible Celery task support for multiple plugins.

Main Classes:
- PluginTaskConfig: Plugin task configuration
- PluginTaskRegistry: Central management of plugin tasks (singleton)

Operation ID Allocation Ranges:
- 1-99: Core operations (JobOperation enum)
- 100-199: custom_view (always reserved)
- 200-9999: Plugin operations (specified in settings.py)
"""

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, Callable

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from airone.lib.log import Logger

logger = Logger


TaskHandler: Callable[[Any, Any], Any] = Callable[[Any, Any], Any]


@dataclass
class PluginTaskConfig:
    """Data class for managing plugin task configuration

    Attributes:
        plugin_id: Plugin identifier (unique within the environment)
        module_path: Module path where Celery tasks are defined
        tasks: Mapping of operation name → (offset, task function name)
               Offset is specified in PLUGIN_OPERATION_ID_CONFIG in settings.py
               Relative position from the range start value (starting from 0)
        hidden_operations: List of operations not shown in UI (default: empty)
        cancelable_operations: List of operations that can be canceled (default: empty)
        parallelizable_operations: List of operations that can run in parallel
        downloadable_operations: List of operations that can be downloaded (default: empty)

    Note:
        The key in tasks is the operation name, and the value is a tuple of (offset, function name).
        Actual operation_id = range_start + offset.
    """

    plugin_id: str
    module_path: str
    tasks: dict[str, tuple[int, str]] = field(default_factory=dict)
    hidden_operations: list[str] = field(default_factory=list)
    cancelable_operations: list[str] = field(default_factory=list)
    parallelizable_operations: list[str] = field(default_factory=list)
    downloadable_operations: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validation after initialization"""
        if not self.plugin_id:
            raise ValueError("plugin_id is required")
        if not self.module_path:
            raise ValueError("module_path is required")
        if not self.tasks:
            raise ValueError(f"No tasks defined for plugin '{self.plugin_id}'")

        for op_name, task_info in self.tasks.items():
            if not isinstance(task_info, tuple) or len(task_info) != 2:
                raise ValueError(
                    f"Task value for operation '{op_name}' in plugin '{self.plugin_id}' "
                    f"must be a tuple of (offset: int, func_name: str)"
                )
            offset, func_name = task_info
            if not isinstance(offset, int) or offset < 0:
                raise ValueError(
                    f"Offset {offset} for operation '{op_name}' in plugin '{self.plugin_id}' "
                    f"must be a non-negative integer"
                )
            if not isinstance(func_name, str):
                raise ValueError(
                    f"Function name for operation '{op_name}' in plugin '{self.plugin_id}' "
                    f"must be a string"
                )

        self.hidden_operations = self.hidden_operations or []
        self.cancelable_operations = self.cancelable_operations or []
        self.parallelizable_operations = self.parallelizable_operations or []
        self.downloadable_operations = self.downloadable_operations or []


class PluginTaskRegistry:
    """Central registry for managing plugin tasks (singleton)

    Responsibilities:
    1. Registration and management of plugin configurations
    2. Allocation of operation_id (referencing PLUGIN_OPERATION_ID_CONFIG in settings.py)
    3. Reverse lookup from operation_id to task handler
    4. Validation at startup (ID conflicts, range overflows, etc.)

    Usage:
        # Register on plugin side
        config = PluginTaskConfig(
            plugin_id="my_plugin",
            module_path="my_plugin.tasks",
            tasks={"process_custom": "process_my_custom_operation"},
        )
        PluginTaskRegistry.register(config)

        # Get operation_id when creating Job
        op_id = PluginTaskRegistry.get_operation_id("my_plugin", "process_custom")

        # Get task handler
        handler = PluginTaskRegistry.get_task_handler(op_id)
    """

    # Class variables (singleton state)
    _registry: dict[str, PluginTaskConfig] = {}
    _operation_id_map: dict[tuple[str, str], int] = {}  # (plugin_id, op_name) -> operation_id
    _reverse_map: dict[int, tuple[str, str]] = {}  # operation_id -> (plugin_id, op_name)
    _initialized = False

    @classmethod
    def register(cls, config: PluginTaskConfig) -> None:
        """Register plugin configuration

        Args:
            config: PluginTaskConfig instance

        Raises:
            ValueError: If plugin is already registered
        """
        if config.plugin_id in cls._registry:
            raise ValueError(f"Plugin '{config.plugin_id}' is already registered")

        cls._registry[config.plugin_id] = config
        logger.info(f"Plugin '{config.plugin_id}' registered")

    @classmethod
    def validate_all(cls) -> None:
        """Validate operation_id ranges for all plugins at startup

        Validation checks:
        1. Conflicts with core operation range (1-99)
        2. Conflicts with custom_view range (100-199)
        3. Range overlaps between plugins
        4. Detection of plugins not specified in settings.py
        5. Verify offsets do not exceed range

        Raises:
            ImproperlyConfigured: If validation fails

        Note:
            This method is called by Django's AppConfig.ready()
        """
        if cls._initialized:
            return

        config = getattr(settings, "PLUGIN_OPERATION_ID_CONFIG", {})
        used_ids: set[int] = set()
        errors: list[str] = []

        # Pre-occupy core and custom_view ranges
        used_ids.update(range(1, 100))  # core
        used_ids.update(range(100, 200))  # custom_view

        for plugin_id, operation_id_range in config.items():
            if not isinstance(operation_id_range, tuple) or len(operation_id_range) != 2:
                errors.append(
                    f"Operation ID range for plugin '{plugin_id}' must be a tuple of "
                    f"(start: int, end: int). Example: (5000, 5099)"
                )
                continue

            range_start, range_end = operation_id_range

            # Check if plugin is actually registered
            if plugin_id not in cls._registry:
                errors.append(
                    f"Plugin '{plugin_id}' is configured in PLUGIN_OPERATION_ID_CONFIG "
                    f"but not registered. Call PluginTaskRegistry.register() in the "
                    f"plugin's AppConfig.ready()."
                )
                continue

            config_obj = cls._registry[plugin_id]

            # Validate range bounds
            if range_start < 200 or range_end > 9999 or range_start > range_end:
                errors.append(
                    f"Operation ID range ({range_start}, {range_end}) for plugin "
                    f"'{plugin_id}' is invalid. Range must be within 200-9999 and "
                    f"start <= end."
                )
                continue

            range_size = range_end - range_start + 1

            for op_name, task_info in config_obj.tasks.items():
                offset, func_name = task_info
                operation_id = range_start + offset

                # Check if offset is within range
                if offset >= range_size:
                    errors.append(
                        f"Offset {offset} for operation '{op_name}' in plugin '{plugin_id}' "
                        f"exceeds range size {range_size}. Range: {range_start}-{range_end}"
                    )
                    continue

                # Check for operation_id conflicts
                if operation_id in used_ids:
                    errors.append(
                        f"Operation ID {operation_id} for operation '{op_name}' in "
                        f"plugin '{plugin_id}' is already in use. Adjust the range "
                        f"in PLUGIN_OPERATION_ID_CONFIG."
                    )
                    continue

                used_ids.add(operation_id)
                cls._operation_id_map[(plugin_id, op_name)] = operation_id
                cls._reverse_map[operation_id] = (plugin_id, op_name)

        if errors:
            error_message = "Plugin operation_id configuration errors:\n" + "\n".join(
                f"  - {error}" for error in errors
            )
            raise ImproperlyConfigured(error_message)

        cls._initialized = True
        logger.info(f"Plugin operation_id validation completed ({len(used_ids)} IDs)")

    @classmethod
    def get_operation_id(cls, plugin_id: str, operation_name: str) -> int:
        """Get operation_id from plugin operation name

        Args:
            plugin_id: Plugin identifier
            operation_name: Operation name

        Returns:
            operation_id

        Raises:
            ValueError: If plugin or operation not found
        """
        key = (plugin_id, operation_name)
        if key not in cls._operation_id_map:
            raise ValueError(
                f"operation_id not found: {plugin_id}:{operation_name}\n"
                f"Must be configured in PLUGIN_OPERATION_ID_CONFIG in settings.py"
            )
        return cls._operation_id_map[key]

    @classmethod
    def get_task_handler(cls, operation_id: int) -> TaskHandler:
        """Get task handler from operation_id

        Args:
            operation_id: operation_id

        Returns:
            Task handler function

        Raises:
            ValueError: If operation_id not found
            AttributeError: If task function not found
        """
        if operation_id not in cls._reverse_map:
            raise ValueError(f"Invalid operation_id: {operation_id}")

        plugin_id, op_name = cls._reverse_map[operation_id]
        config = cls._registry[plugin_id]

        # Dynamically import task module
        module = import_module(config.module_path)

        offset, func_name = config.tasks[op_name]
        handler = getattr(module, func_name, None)
        if handler is None:
            raise AttributeError(f"Task function not found: {config.module_path}.{func_name}")
        return handler

    @classmethod
    def get_all_tasks(cls) -> dict[int, tuple[str, str]]:
        """Get task information for all plugins

        Returns:
            {operation_id: (module_path, function_name)}
        """
        result = {}
        for (plugin_id, op_name), op_id in cls._operation_id_map.items():
            config = cls._registry[plugin_id]
            offset, func_name = config.tasks[op_name]
            result[op_id] = (config.module_path, func_name)
        return result

    @classmethod
    def get_all_configs(cls) -> dict[str, PluginTaskConfig]:
        """Get configuration for all plugins

        Returns:
            {plugin_id: PluginTaskConfig} dict
        """
        return cls._registry.copy()

    @classmethod
    def reset(cls) -> None:
        """Reset registry (for testing)"""
        cls._registry.clear()
        cls._operation_id_map.clear()
        cls._reverse_map.clear()
        cls._initialized = False


def register_plugin_job_task(offset: int) -> Callable:
    """
    Decorator for plugin tasks that associates an operation_id with a Celery task.
    Similar to @register_job_task on the core side, it only takes a numeric offset.

    Actual job method registration is performed by dynamic loading in Job.method_table().

    Args:
        offset: Offset of operation_id
               Actual operation_id = range_start specified in PLUGIN_OPERATION_ID_CONFIG + offset

    Returns:
        Decorator function

    Example:
        @register_plugin_job_task(0)
        @app.task(bind=True)
        def hello_world_task(self, job_id: int):
            job = Job.objects.get(id=job_id)
            if job.is_canceled():
                return JobStatus.CANCELED
            if not job.proceed_if_ready():
                return
            job.update(JobStatus.PROCESSING)
            try:
                # ... task processing ...
                job.update(JobStatus.DONE)
            except Exception as e:
                logger.error(f"Task failed: {str(e)}")
                job.update(JobStatus.ERROR)
    """

    def decorator(func: TaskHandler) -> TaskHandler:
        func._offset = offset
        logger.info(f"Plugin task '{func.__module__}.{func.__name__}' (offset={offset}) decorated")
        return func

    return decorator
