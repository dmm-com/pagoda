"""
Celery task configuration for Hello World Plugin

This module defines the plugin's task operations and their configuration
for use with Airone's plugin task registry system.
"""

import enum

from pagoda_plugin_sdk.models import PluginSchema, PluginSchemaConfig
from pagoda_plugin_sdk.tasks import PluginTaskConfig


class HelloWorldPluginOperation(int, enum.Enum):
    """Operation offsets for Hello World Plugin

    These offsets are used in the registry to calculate actual operation_ids.
    operation_id = PLUGIN_OPERATION_ID_CONFIG["hello-world"][0] + offset
    """

    HELLO_WORLD_TASK = 0


PLUGIN_TASK_CONFIG = PluginTaskConfig(
    plugin_id="hello-world",
    module_path="pagoda_hello_world_plugin.tasks",
    tasks={
        "hello_world_task": (
            HelloWorldPluginOperation.HELLO_WORLD_TASK,
            "hello_world_task",
        ),
    },
    hidden_operations=[],
    cancelable_operations=[],
    parallelizable_operations=[],
    downloadable_operations=[],
)

PLUGIN_MODEL_CONFIG = PluginSchemaConfig(
    plugin_id="hello-world",
    schema={
        "book": PluginSchema(
            **{
                "name": "書籍",
                "attrs": {
                    "author": {"name": "著者", "type": "string"},
                    "age": {"name": "年齢", "type": "number"},
                },
            }
        ),
    },
)
