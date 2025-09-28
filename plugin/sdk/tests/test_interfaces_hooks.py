"""
Tests for hook interface.

Tests the HookInterface protocol and its implementations
to ensure proper hook registration, execution, and management functionality.
"""

import unittest

from pagoda_plugin_sdk.interfaces.hooks import COMMON_HOOKS, HookInterface


class TestHookInterface(unittest.TestCase):
    """Test cases for HookInterface"""

    def test_hook_interface_is_abstract(self):
        """Test that HookInterface cannot be instantiated directly"""
        with self.assertRaises(TypeError):
            HookInterface()

    def test_hook_interface_requires_abstract_methods(self):
        """Test that subclasses must implement abstract methods"""

        class IncompleteHookImpl(HookInterface):
            def register_hook(self, hook_name, callback, priority=50):
                return True

            # Missing other abstract methods

        with self.assertRaises(TypeError):
            IncompleteHookImpl()


class MockHookImplementation(HookInterface):
    """Mock implementation of HookInterface for testing"""

    def __init__(self):
        # Store hooks as {hook_name: [(callback, priority), ...]}
        self.hooks = {}
        # Available hooks that can be registered
        self.available_hooks = COMMON_HOOKS.copy()
        # Track execution order
        self.execution_log = []

    def register_hook(self, hook_name, callback, priority=50):
        """Register a hook callback"""
        if not hook_name:
            return False

        if not callable(callback):
            return False

        if hook_name not in self.hooks:
            self.hooks[hook_name] = []

        # Check if callback is already registered
        for existing_callback, _ in self.hooks[hook_name]:
            if existing_callback == callback:
                return False  # Already registered

        self.hooks[hook_name].append((callback, priority))
        # Sort by priority (lower numbers execute first)
        self.hooks[hook_name].sort(key=lambda x: x[1])

        return True

    def unregister_hook(self, hook_name, callback):
        """Unregister a hook callback"""
        if hook_name not in self.hooks:
            return False

        original_length = len(self.hooks[hook_name])
        self.hooks[hook_name] = [(cb, pri) for cb, pri in self.hooks[hook_name] if cb != callback]

        # Return True if something was removed
        return len(self.hooks[hook_name]) < original_length

    def execute_hook(self, hook_name, *args, **kwargs):
        """Execute all callbacks registered for a hook"""
        if hook_name not in self.hooks:
            return []

        results = []
        for callback, priority in self.hooks[hook_name]:
            try:
                result = callback(*args, **kwargs)
                results.append(result)
                self.execution_log.append(
                    {"hook": hook_name, "callback": callback.__name__, "priority": priority}
                )
            except Exception as e:
                # In a real implementation, you might want to handle this differently
                results.append(f"Error: {str(e)}")

        return results

    def get_available_hooks(self):
        """Get list of available hook names"""
        return self.available_hooks.copy()

    def get_hook_callbacks(self, hook_name):
        """Get all callbacks registered for a hook (custom implementation)"""
        if hook_name not in self.hooks:
            return []
        return [callback for callback, _ in self.hooks[hook_name]]

    def clear_hook_callbacks(self, hook_name):
        """Clear all callbacks for a hook (custom implementation)"""
        if hook_name in self.hooks:
            self.hooks[hook_name] = []
            return True
        return False

    def add_available_hook(self, hook_name):
        """Helper method to add new available hooks for testing"""
        if hook_name not in self.available_hooks:
            self.available_hooks.append(hook_name)


class TestMockHookImplementation(unittest.TestCase):
    """Test cases for MockHookImplementation"""

    def setUp(self):
        """Set up test fixtures"""
        self.hooks = MockHookImplementation()

    def test_register_hook_success(self):
        """Test successful hook registration"""

        def test_callback():
            return "test result"

        result = self.hooks.register_hook("entry.after_create", test_callback)
        self.assertTrue(result)

        # Verify callback is registered
        callbacks = self.hooks.get_hook_callbacks("entry.after_create")
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(callbacks[0], test_callback)

    def test_register_hook_with_priority(self):
        """Test hook registration with custom priority"""

        def high_priority():
            return "high"

        def low_priority():
            return "low"

        # Register in reverse order of priority
        self.hooks.register_hook("entry.after_create", low_priority, priority=100)
        self.hooks.register_hook("entry.after_create", high_priority, priority=10)

        # Execute and verify order
        results = self.hooks.execute_hook("entry.after_create")
        self.assertEqual(results, ["high", "low"])

    def test_register_hook_duplicate_callback(self):
        """Test registering the same callback twice"""

        def test_callback():
            return "test"

        # First registration should succeed
        result1 = self.hooks.register_hook("entry.after_create", test_callback)
        self.assertTrue(result1)

        # Second registration should fail
        result2 = self.hooks.register_hook("entry.after_create", test_callback)
        self.assertFalse(result2)

        # Should only have one callback
        callbacks = self.hooks.get_hook_callbacks("entry.after_create")
        self.assertEqual(len(callbacks), 1)

    def test_register_hook_invalid_callback(self):
        """Test registering non-callable as callback"""
        result = self.hooks.register_hook("entry.after_create", "not a function")
        self.assertFalse(result)

        result = self.hooks.register_hook("entry.after_create", None)
        self.assertFalse(result)

    def test_register_hook_empty_name(self):
        """Test registering hook with empty name"""

        def test_callback():
            pass

        result = self.hooks.register_hook("", test_callback)
        self.assertFalse(result)

    def test_unregister_hook_success(self):
        """Test successful hook unregistration"""

        def test_callback():
            return "test"

        # Register first
        self.hooks.register_hook("entry.after_create", test_callback)
        self.assertEqual(len(self.hooks.get_hook_callbacks("entry.after_create")), 1)

        # Unregister
        result = self.hooks.unregister_hook("entry.after_create", test_callback)
        self.assertTrue(result)
        self.assertEqual(len(self.hooks.get_hook_callbacks("entry.after_create")), 0)

    def test_unregister_hook_nonexistent_hook(self):
        """Test unregistering from nonexistent hook"""

        def test_callback():
            pass

        result = self.hooks.unregister_hook("nonexistent.hook", test_callback)
        self.assertFalse(result)

    def test_unregister_hook_nonexistent_callback(self):
        """Test unregistering nonexistent callback"""

        def registered_callback():
            pass

        def unregistered_callback():
            pass

        # Register one callback
        self.hooks.register_hook("entry.after_create", registered_callback)

        # Try to unregister different callback
        result = self.hooks.unregister_hook("entry.after_create", unregistered_callback)
        self.assertFalse(result)

        # Original callback should still be there
        callbacks = self.hooks.get_hook_callbacks("entry.after_create")
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(callbacks[0], registered_callback)

    def test_execute_hook_with_arguments(self):
        """Test executing hook with arguments"""

        def callback_with_args(arg1, arg2, kwarg1=None):
            return f"args: {arg1}, {arg2}, kwarg: {kwarg1}"

        self.hooks.register_hook("entry.after_create", callback_with_args)

        results = self.hooks.execute_hook(
            "entry.after_create", "value1", "value2", kwarg1="kw_value"
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "args: value1, value2, kwarg: kw_value")

    def test_execute_hook_nonexistent_hook(self):
        """Test executing nonexistent hook"""
        results = self.hooks.execute_hook("nonexistent.hook")
        self.assertEqual(results, [])

    def test_execute_hook_with_exception(self):
        """Test executing hook when callback raises exception"""

        def failing_callback():
            raise ValueError("Test error")

        def working_callback():
            return "success"

        self.hooks.register_hook("entry.after_create", failing_callback)
        self.hooks.register_hook("entry.after_create", working_callback)

        results = self.hooks.execute_hook("entry.after_create")
        self.assertEqual(len(results), 2)
        self.assertIn("Error: Test error", results[0])
        self.assertEqual(results[1], "success")

    def test_execute_hook_priority_order(self):
        """Test that hooks execute in priority order"""

        def callback_priority_1():
            return "first"

        def callback_priority_2():
            return "second"

        def callback_priority_3():
            return "third"

        # Register in non-priority order
        self.hooks.register_hook("entry.after_create", callback_priority_2, priority=20)
        self.hooks.register_hook("entry.after_create", callback_priority_3, priority=30)
        self.hooks.register_hook("entry.after_create", callback_priority_1, priority=10)

        results = self.hooks.execute_hook("entry.after_create")
        self.assertEqual(results, ["first", "second", "third"])

    def test_get_available_hooks(self):
        """Test getting available hooks"""
        available = self.hooks.get_available_hooks()

        # Should include common hooks
        self.assertIn("entry.after_create", available)
        self.assertIn("entity.before_update", available)
        self.assertIn("user.after_login", available)

        # Should be a copy (modifying returned list shouldn't affect original)
        original_length = len(available)
        available.append("test.hook")
        new_available = self.hooks.get_available_hooks()
        self.assertEqual(len(new_available), original_length)

    def test_hook_exists_with_available_hook(self):
        """Test hook_exists with available hook"""
        result = self.hooks.hook_exists("entry.after_create")
        self.assertTrue(result)

    def test_hook_exists_with_unavailable_hook(self):
        """Test hook_exists with unavailable hook"""
        result = self.hooks.hook_exists("nonexistent.hook")
        self.assertFalse(result)

    def test_hook_exists_with_added_hook(self):
        """Test hook_exists after adding new available hook"""
        # Initially doesn't exist
        self.assertFalse(self.hooks.hook_exists("custom.hook"))

        # Add to available hooks
        self.hooks.add_available_hook("custom.hook")

        # Now it exists
        self.assertTrue(self.hooks.hook_exists("custom.hook"))

    def test_get_hook_callbacks_empty(self):
        """Test getting callbacks for hook with no callbacks"""
        callbacks = self.hooks.get_hook_callbacks("entry.after_create")
        self.assertEqual(callbacks, [])

    def test_get_hook_callbacks_nonexistent_hook(self):
        """Test getting callbacks for nonexistent hook"""
        callbacks = self.hooks.get_hook_callbacks("nonexistent.hook")
        self.assertEqual(callbacks, [])

    def test_clear_hook_callbacks_success(self):
        """Test clearing hook callbacks"""

        def test_callback1():
            pass

        def test_callback2():
            pass

        # Register callbacks
        self.hooks.register_hook("entry.after_create", test_callback1)
        self.hooks.register_hook("entry.after_create", test_callback2)
        self.assertEqual(len(self.hooks.get_hook_callbacks("entry.after_create")), 2)

        # Clear callbacks
        result = self.hooks.clear_hook_callbacks("entry.after_create")
        self.assertTrue(result)
        self.assertEqual(len(self.hooks.get_hook_callbacks("entry.after_create")), 0)

    def test_clear_hook_callbacks_nonexistent_hook(self):
        """Test clearing callbacks for nonexistent hook"""
        result = self.hooks.clear_hook_callbacks("nonexistent.hook")
        self.assertFalse(result)

    def test_execution_logging(self):
        """Test that hook execution is logged"""

        def callback1():
            return "result1"

        def callback2():
            return "result2"

        self.hooks.register_hook("entry.after_create", callback1, priority=10)
        self.hooks.register_hook("entry.after_create", callback2, priority=20)

        self.hooks.execute_hook("entry.after_create")

        # Check execution log
        self.assertEqual(len(self.hooks.execution_log), 2)
        self.assertEqual(self.hooks.execution_log[0]["hook"], "entry.after_create")
        self.assertEqual(self.hooks.execution_log[0]["callback"], "callback1")
        self.assertEqual(self.hooks.execution_log[0]["priority"], 10)


class TestCommonHooks(unittest.TestCase):
    """Test cases for COMMON_HOOKS constant"""

    def test_common_hooks_contains_expected_hooks(self):
        """Test that COMMON_HOOKS contains expected hook names"""
        # Entity lifecycle hooks
        self.assertIn("entity.before_create", COMMON_HOOKS)
        self.assertIn("entity.after_create", COMMON_HOOKS)
        self.assertIn("entity.before_update", COMMON_HOOKS)
        self.assertIn("entity.after_update", COMMON_HOOKS)

        # Entry lifecycle hooks
        self.assertIn("entry.before_create", COMMON_HOOKS)
        self.assertIn("entry.after_create", COMMON_HOOKS)
        self.assertIn("entry.before_delete", COMMON_HOOKS)
        self.assertIn("entry.after_delete", COMMON_HOOKS)

        # User/Authentication hooks
        self.assertIn("user.after_login", COMMON_HOOKS)
        self.assertIn("user.after_logout", COMMON_HOOKS)

        # System hooks
        self.assertIn("system.startup", COMMON_HOOKS)
        self.assertIn("system.shutdown", COMMON_HOOKS)

    def test_common_hooks_is_list(self):
        """Test that COMMON_HOOKS is a list"""
        self.assertIsInstance(COMMON_HOOKS, list)

    def test_common_hooks_contains_strings(self):
        """Test that all COMMON_HOOKS entries are strings"""
        for hook in COMMON_HOOKS:
            self.assertIsInstance(hook, str)
            self.assertGreater(len(hook), 0)

    def test_common_hooks_no_duplicates(self):
        """Test that COMMON_HOOKS contains no duplicates"""
        self.assertEqual(len(COMMON_HOOKS), len(set(COMMON_HOOKS)))


class TestHookInterfaceDefaultMethods(unittest.TestCase):
    """Test cases for HookInterface default method implementations"""

    def test_hook_exists_default_implementation(self):
        """Test that default hook_exists uses get_available_hooks"""

        class MinimalHookImpl(HookInterface):
            def register_hook(self, hook_name, callback, priority=50):
                return True

            def unregister_hook(self, hook_name, callback):
                return True

            def execute_hook(self, hook_name, *args, **kwargs):
                return []

            def get_available_hooks(self):
                return ["test.hook", "another.hook"]

        hooks = MinimalHookImpl()

        self.assertTrue(hooks.hook_exists("test.hook"))
        self.assertTrue(hooks.hook_exists("another.hook"))
        self.assertFalse(hooks.hook_exists("nonexistent.hook"))

    def test_get_hook_callbacks_default_implementation(self):
        """Test that default get_hook_callbacks returns empty list"""

        class MinimalHookImpl(HookInterface):
            def register_hook(self, hook_name, callback, priority=50):
                return True

            def unregister_hook(self, hook_name, callback):
                return True

            def execute_hook(self, hook_name, *args, **kwargs):
                return []

            def get_available_hooks(self):
                return []

        hooks = MinimalHookImpl()
        result = hooks.get_hook_callbacks("any.hook")
        self.assertEqual(result, [])

    def test_clear_hook_callbacks_default_implementation(self):
        """Test that default clear_hook_callbacks returns False"""

        class MinimalHookImpl(HookInterface):
            def register_hook(self, hook_name, callback, priority=50):
                return True

            def unregister_hook(self, hook_name, callback):
                return True

            def execute_hook(self, hook_name, *args, **kwargs):
                return []

            def get_available_hooks(self):
                return []

        hooks = MinimalHookImpl()
        result = hooks.clear_hook_callbacks("any.hook")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
