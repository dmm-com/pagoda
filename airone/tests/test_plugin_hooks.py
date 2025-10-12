"""
Tests for Plugin Hooks module

Tests hook name normalization, validation, and metadata functions.
"""

import unittest

from airone.plugins.hooks import (
    AVAILABLE_HOOKS,
    HOOK_ALIASES,
    HOOK_ALIASES_REVERSE,
    HOOK_METADATA,
    get_hook_metadata,
    get_legacy_hook_name,
    is_valid_hook_name,
    list_available_hooks,
    list_legacy_hook_names,
    normalize_hook_name,
)


class TestPluginHooks(unittest.TestCase):
    """Test cases for plugin hooks module"""

    def test_normalize_hook_name_standard(self):
        """Test normalizing already standard hook names"""
        self.assertEqual(normalize_hook_name("entry.after_create"), "entry.after_create")
        self.assertEqual(normalize_hook_name("entry.before_update"), "entry.before_update")
        self.assertEqual(normalize_hook_name("entity.after_create"), "entity.after_create")

    def test_normalize_hook_name_legacy(self):
        """Test normalizing legacy custom_view hook names"""
        self.assertEqual(normalize_hook_name("after_create_entry_v2"), "entry.after_create")
        self.assertEqual(normalize_hook_name("before_update_entry_v2"), "entry.before_update")
        self.assertEqual(normalize_hook_name("validate_entry"), "entry.validate")
        self.assertEqual(normalize_hook_name("get_entry_attr"), "entry.get_attrs")

    def test_normalize_hook_name_unknown(self):
        """Test normalizing unknown hook names returns original"""
        self.assertEqual(normalize_hook_name("unknown_hook"), "unknown_hook")
        self.assertEqual(normalize_hook_name("custom.hook"), "custom.hook")

    def test_get_legacy_hook_name(self):
        """Test converting standard hook names to legacy names"""
        self.assertEqual(get_legacy_hook_name("entry.after_create"), "after_create_entry_v2")
        self.assertEqual(get_legacy_hook_name("entry.before_update"), "before_update_entry_v2")
        self.assertEqual(get_legacy_hook_name("entry.validate"), "validate_entry")

    def test_get_legacy_hook_name_no_mapping(self):
        """Test getting legacy name for unmapped hooks returns original"""
        self.assertEqual(get_legacy_hook_name("unknown.hook"), "unknown.hook")

    def test_is_valid_hook_name_standard(self):
        """Test validating standard hook names"""
        self.assertTrue(is_valid_hook_name("entry.after_create"))
        self.assertTrue(is_valid_hook_name("entry.before_update"))
        self.assertTrue(is_valid_hook_name("entity.after_create"))
        self.assertTrue(is_valid_hook_name("entry.validate"))

    def test_is_valid_hook_name_legacy(self):
        """Test validating legacy hook names"""
        self.assertTrue(is_valid_hook_name("after_create_entry_v2"))
        self.assertTrue(is_valid_hook_name("before_update_entry_v2"))
        self.assertTrue(is_valid_hook_name("validate_entry"))
        self.assertTrue(is_valid_hook_name("get_entry_attr"))

    def test_is_valid_hook_name_invalid(self):
        """Test validating invalid hook names"""
        self.assertFalse(is_valid_hook_name("unknown_hook"))
        self.assertFalse(is_valid_hook_name("custom.hook"))
        self.assertFalse(is_valid_hook_name(""))

    def test_get_hook_metadata(self):
        """Test getting hook metadata"""
        metadata = get_hook_metadata("entry.after_create")
        self.assertIn("description", metadata)
        self.assertIn("args", metadata)
        self.assertIn("returns", metadata)
        self.assertEqual(metadata["description"], "Called after an entry is created")

    def test_get_hook_metadata_legacy_name(self):
        """Test getting metadata using legacy hook name"""
        metadata = get_hook_metadata("after_create_entry_v2")
        self.assertIn("description", metadata)
        self.assertEqual(metadata["description"], "Called after an entry is created")

    def test_get_hook_metadata_unknown(self):
        """Test getting metadata for unknown hook returns empty dict"""
        metadata = get_hook_metadata("unknown_hook")
        self.assertEqual(metadata, {})

    def test_list_available_hooks(self):
        """Test getting list of available hooks"""
        hooks = list_available_hooks()
        self.assertIsInstance(hooks, list)
        self.assertGreater(len(hooks), 0)
        self.assertIn("entry.after_create", hooks)
        self.assertIn("entry.validate", hooks)
        self.assertIn("entity.after_create", hooks)

    def test_list_available_hooks_returns_copy(self):
        """Test that list_available_hooks returns a copy, not reference"""
        hooks1 = list_available_hooks()
        hooks2 = list_available_hooks()
        self.assertIsNot(hooks1, hooks2)
        self.assertEqual(hooks1, hooks2)

    def test_list_legacy_hook_names(self):
        """Test getting list of legacy hook names"""
        legacy_names = list_legacy_hook_names()
        self.assertIsInstance(legacy_names, list)
        self.assertGreater(len(legacy_names), 0)
        self.assertIn("after_create_entry_v2", legacy_names)
        self.assertIn("validate_entry", legacy_names)
        self.assertIn("get_entry_attr", legacy_names)

    def test_hook_aliases_bidirectional(self):
        """Test that HOOK_ALIASES and HOOK_ALIASES_REVERSE are consistent"""
        for legacy, standard in HOOK_ALIASES.items():
            self.assertEqual(HOOK_ALIASES_REVERSE[standard], legacy)

    def test_all_available_hooks_have_metadata(self):
        """Test that all available hooks have metadata defined"""
        for hook_name in AVAILABLE_HOOKS:
            self.assertIn(hook_name, HOOK_METADATA, f"Hook '{hook_name}' missing metadata")

    def test_all_metadata_hooks_are_available(self):
        """Test that all hooks in metadata are in available hooks"""
        for hook_name in HOOK_METADATA.keys():
            self.assertIn(
                hook_name, AVAILABLE_HOOKS, f"Metadata defined for unavailable hook '{hook_name}'"
            )

    def test_hook_metadata_structure(self):
        """Test that hook metadata has required fields"""
        required_fields = {"description", "args", "returns"}
        for hook_name, metadata in HOOK_METADATA.items():
            for field in required_fields:
                self.assertIn(
                    field, metadata, f"Hook '{hook_name}' missing required field '{field}'"
                )


if __name__ == "__main__":
    unittest.main()
