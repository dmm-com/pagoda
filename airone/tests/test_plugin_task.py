"""Plugin task registry tests"""

import sys
from types import ModuleType

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from airone.lib.plugin_task import (
    PluginTaskConfig,
    PluginTaskRegistry,
)
from job.models import Job


class TestPluginTaskConfig(TestCase):
    """PluginTaskConfig tests"""

    def test_create_with_required_fields(self):
        """Create with required fields"""
        config = PluginTaskConfig(
            plugin_id="test_plugin",
            module_path="test_plugin.tasks",
            tasks={"operation_a": (0, "task_a")},
        )
        self.assertEqual(config.plugin_id, "test_plugin")
        self.assertEqual(config.module_path, "test_plugin.tasks")
        self.assertEqual(config.tasks, {"operation_a": (0, "task_a")})

    def test_create_with_operation_attributes(self):
        """Create with operation attributes"""
        config = PluginTaskConfig(
            plugin_id="test_plugin",
            module_path="test_plugin.tasks",
            tasks={"operation_a": (0, "task_a")},
            hidden_operations=["operation_a"],
            cancelable_operations=["operation_a"],
            parallelizable_operations=["operation_a"],
            downloadable_operations=["operation_a"],
        )
        self.assertEqual(config.hidden_operations, ["operation_a"])
        self.assertEqual(config.cancelable_operations, ["operation_a"])
        self.assertEqual(config.parallelizable_operations, ["operation_a"])
        self.assertEqual(config.downloadable_operations, ["operation_a"])

    def test_missing_plugin_id_raises_error(self):
        """Raise error when plugin_id is missing"""
        with self.assertRaises(ValueError):
            PluginTaskConfig(
                plugin_id="",
                module_path="test_plugin.tasks",
                tasks={"operation_a": (0, "task_a")},
            )

    def test_missing_module_path_raises_error(self):
        """Raise error when module_path is missing"""
        with self.assertRaises(ValueError):
            PluginTaskConfig(
                plugin_id="test_plugin",
                module_path="",
                tasks={"operation_a": (0, "task_a")},
            )

    def test_missing_tasks_raises_error(self):
        """Raise error when tasks is empty"""
        with self.assertRaises(ValueError):
            PluginTaskConfig(
                plugin_id="test_plugin",
                module_path="test_plugin.tasks",
                tasks={},
            )


class TestPluginTaskRegistry(TestCase):
    """PluginTaskRegistry tests"""

    def setUp(self):
        """Reset registry before each test"""
        PluginTaskRegistry.reset()

    def tearDown(self):
        """Reset registry after each test"""
        PluginTaskRegistry.reset()

    def test_duplicate_registration_raises_error(self):
        """Raise error when registering same plugin twice"""
        config = PluginTaskConfig(
            plugin_id="test_plugin",
            module_path="test_plugin.tasks",
            tasks={"operation_a": (0, "task_a")},
        )
        PluginTaskRegistry.register(config)

        with self.assertRaises(ValueError) as ctx:
            PluginTaskRegistry.register(config)

        self.assertIn("既に登録されています", str(ctx.exception))

    def test_get_all_configs(self):
        """Get all plugin configurations"""
        config1 = PluginTaskConfig(
            plugin_id="plugin1",
            module_path="plugin1.tasks",
            tasks={"op_a": (0, "task_a")},
        )
        config2 = PluginTaskConfig(
            plugin_id="plugin2",
            module_path="plugin2.tasks",
            tasks={"op_b": (0, "task_b")},
        )
        PluginTaskRegistry.register(config1)
        PluginTaskRegistry.register(config2)

        configs = PluginTaskRegistry.get_all_configs()
        self.assertEqual(len(configs), 2)
        self.assertIn("plugin1", configs)
        self.assertIn("plugin2", configs)

    @override_settings(
        PLUGIN_OPERATION_ID_CONFIG={
            "test_plugin": (5000, 5099),
        }
    )
    def test_validate_all_success(self):
        """Validate successfully"""
        config = PluginTaskConfig(
            plugin_id="test_plugin",
            module_path="test_plugin.tasks",
            tasks={
                "operation_a": (0, "task_a"),
                "operation_b": (1, "task_b"),
            },
        )
        PluginTaskRegistry.register(config)

        PluginTaskRegistry.validate_all()
        self.assertTrue(True)

    def test_validate_all_unregistered_plugin_raises_error(self):
        """Plugin configured in settings but not registered"""
        with override_settings(
            PLUGIN_OPERATION_ID_CONFIG={
                "missing_plugin": (5000, 5099),
            }
        ):
            PluginTaskRegistry.reset()

            with self.assertRaises(ImproperlyConfigured) as ctx:
                PluginTaskRegistry.validate_all()

            self.assertIn("missing_plugin", str(ctx.exception))
            self.assertIn("登録されていません", str(ctx.exception))

    def test_validate_all_offset_exceeds_range(self):
        """Offset exceeds range"""
        with override_settings(
            PLUGIN_OPERATION_ID_CONFIG={
                "test_plugin": (5000, 5099),
            }
        ):
            config = PluginTaskConfig(
                plugin_id="test_plugin",
                module_path="test_plugin.tasks",
                tasks={"operation_a": (100, "task_a")},
            )
            PluginTaskRegistry.register(config)

            with self.assertRaises(ImproperlyConfigured) as ctx:
                PluginTaskRegistry.validate_all()

            self.assertIn("レンジサイズ", str(ctx.exception))

    def test_validate_all_invalid_operation_id_range(self):
        """Invalid operation_id range"""
        with override_settings(
            PLUGIN_OPERATION_ID_CONFIG={
                "test_plugin": (50, 100),
            }
        ):
            config = PluginTaskConfig(
                plugin_id="test_plugin",
                module_path="test_plugin.tasks",
                tasks={"operation_a": (0, "task_a")},
            )
            PluginTaskRegistry.register(config)

            with self.assertRaises(ImproperlyConfigured) as ctx:
                PluginTaskRegistry.validate_all()

            self.assertIn("不正です", str(ctx.exception))

    def test_validate_all_custom_view_range_conflict(self):
        """Conflict with custom_view reserved range"""
        with override_settings(
            PLUGIN_OPERATION_ID_CONFIG={
                "test_plugin": (100, 150),
            }
        ):
            config = PluginTaskConfig(
                plugin_id="test_plugin",
                module_path="test_plugin.tasks",
                tasks={"operation_a": (0, "task_a")},
            )
            PluginTaskRegistry.register(config)

            with self.assertRaises(ImproperlyConfigured) as ctx:
                PluginTaskRegistry.validate_all()

            self.assertIn("不正です", str(ctx.exception))

    def test_validate_all_duplicate_operation_id(self):
        """Duplicate operation_id when ranges overlap between plugins"""
        with override_settings(
            PLUGIN_OPERATION_ID_CONFIG={
                "plugin1": (5000, 5099),
                "plugin2": (5050, 5150),
            }
        ):
            config1 = PluginTaskConfig(
                plugin_id="plugin1",
                module_path="plugin1.tasks",
                tasks={"operation_a": (50, "task_a")},
            )
            config2 = PluginTaskConfig(
                plugin_id="plugin2",
                module_path="plugin2.tasks",
                tasks={"operation_b": (0, "task_b")},
            )
            PluginTaskRegistry.register(config1)
            PluginTaskRegistry.register(config2)

            with self.assertRaises(ImproperlyConfigured) as ctx:
                PluginTaskRegistry.validate_all()

            self.assertIn("既に他の操作で使用されています", str(ctx.exception))

    @override_settings(
        PLUGIN_OPERATION_ID_CONFIG={
            "test_plugin": (5000, 5099),
        }
    )
    def test_get_operation_id(self):
        """Get operation_id"""
        config = PluginTaskConfig(
            plugin_id="test_plugin",
            module_path="test_plugin.tasks",
            tasks={
                "operation_a": (0, "task_a"),
                "operation_b": (1, "task_b"),
            },
        )
        PluginTaskRegistry.register(config)
        PluginTaskRegistry.validate_all()

        op_id_a = PluginTaskRegistry.get_operation_id("test_plugin", "operation_a")
        op_id_b = PluginTaskRegistry.get_operation_id("test_plugin", "operation_b")

        self.assertEqual(op_id_a, 5000)
        self.assertEqual(op_id_b, 5001)

    @override_settings(
        PLUGIN_OPERATION_ID_CONFIG={
            "test_plugin": (5000, 5099),
        }
    )
    def test_get_operation_id_raises_error_for_unknown_operation(self):
        """Raise error for unregistered operation name"""
        config = PluginTaskConfig(
            plugin_id="test_plugin",
            module_path="test_plugin.tasks",
            tasks={"operation_a": (0, "task_a")},
        )
        PluginTaskRegistry.register(config)
        PluginTaskRegistry.validate_all()

        with self.assertRaises(ValueError) as ctx:
            PluginTaskRegistry.get_operation_id("test_plugin", "unknown_operation")

        self.assertIn("見つかりません", str(ctx.exception))

    @override_settings(
        PLUGIN_OPERATION_ID_CONFIG={
            "test_plugin": (5000, 5099),
        }
    )
    def test_get_all_tasks(self):
        """Get all task information"""
        config = PluginTaskConfig(
            plugin_id="test_plugin",
            module_path="test_plugin.tasks",
            tasks={
                "operation_a": (0, "task_a"),
                "operation_b": (1, "task_b"),
            },
        )
        PluginTaskRegistry.register(config)
        PluginTaskRegistry.validate_all()

        tasks = PluginTaskRegistry.get_all_tasks()
        self.assertEqual(tasks[5000], ("test_plugin.tasks", "task_a"))
        self.assertEqual(tasks[5001], ("test_plugin.tasks", "task_b"))


class TestJobMethodTable(TestCase):
    """Job.method_table() plugin task extension tests"""

    def setUp(self):
        """Reset registry before each test"""
        PluginTaskRegistry.reset()

    def tearDown(self):
        """Reset registry after each test"""
        PluginTaskRegistry.reset()

    @override_settings(
        PLUGIN_OPERATION_ID_CONFIG={
            "test_plugin": (5000, 5099),
        }
    )
    def test_method_table_includes_plugin_tasks(self):
        """method_table() includes plugin tasks"""

        # Dummy task functions for testing
        def dummy_task_a(job):
            return None

        def dummy_task_b(job):
            return None

        # Register module in system
        module = ModuleType("test_plugin.tasks")
        module.task_a = dummy_task_a
        module.task_b = dummy_task_b
        sys.modules["test_plugin.tasks"] = module

        try:
            config = PluginTaskConfig(
                plugin_id="test_plugin",
                module_path="test_plugin.tasks",
                tasks={
                    "operation_a": (0, "task_a"),
                    "operation_b": (1, "task_b"),
                },
            )
            PluginTaskRegistry.register(config)
            PluginTaskRegistry.validate_all()

            # Get method_table
            Job._METHOD_TABLE.clear()  # Clear cache
            method_table = Job.method_table()

            # Verify plugin tasks are included
            self.assertIn(5000, method_table)
            self.assertIn(5001, method_table)
            self.assertEqual(method_table[5000], dummy_task_a)
            self.assertEqual(method_table[5001], dummy_task_b)
        finally:
            # Cleanup
            if "test_plugin.tasks" in sys.modules:
                del sys.modules["test_plugin.tasks"]

    @override_settings(
        PLUGIN_OPERATION_ID_CONFIG={
            "test_plugin": (5000, 5099),
        }
    )
    def test_method_table_handles_missing_plugin_gracefully(self):
        """method_table() continues processing when plugin not initialized"""
        # Plugin is not registered and validate_all() is not called

        Job._METHOD_TABLE.clear()
        # No exception should be raised, method table is returned
        method_table = Job.method_table()

        # Only CUSTOM_TASKS should be included
        self.assertIsInstance(method_table, dict)
