"""
Tests for HelloWorldPlugin hook functionality

Tests the behavior of various hooks including:
- Entry lifecycle hooks (create, update, delete)
- Entity lifecycle hooks (create, update)
- Validation hooks
- Get attributes hooks
"""

import unittest
from unittest.mock import MagicMock, patch

from pagoda_hello_world_plugin.plugin import HelloWorldPlugin


class TestEntryHooks(unittest.TestCase):
    """Test cases for entry lifecycle hooks"""

    def setUp(self):
        """Set up test fixtures"""
        self.plugin = HelloWorldPlugin()
        self.mock_user = MagicMock()
        self.mock_user.username = "test_user"
        self.mock_entry = MagicMock()
        self.mock_entry.name = "test_entry"

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_log_helloworld_create(self, mock_logger):
        """Test after_create hook for helloworld entity"""
        self.plugin.log_helloworld_create(
            entity_name="helloworld", user=self.mock_user, entry=self.mock_entry
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("Entry created", call_args)
        self.assertIn("test_entry", call_args)
        self.assertIn("helloworld", call_args)
        self.assertIn("test_user", call_args)

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_log_helloworld_before_update(self, mock_logger):
        """Test before_update hook for helloworld entity"""
        validated_data = {"name": "updated_name"}

        result = self.plugin.log_helloworld_before_update(
            entity_name="helloworld",
            user=self.mock_user,
            validated_data=validated_data,
            entry=self.mock_entry,
        )

        # Check logging
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("Entry updating", call_args)
        self.assertIn("test_entry", call_args)

        # Check that validated_data is returned
        self.assertEqual(result, validated_data)

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_log_helloworld_after_update(self, mock_logger):
        """Test after_update hook for helloworld entity"""
        self.plugin.log_helloworld_after_update(
            entity_name="helloworld", user=self.mock_user, entry=self.mock_entry
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("Entry updated", call_args)
        self.assertIn("test_entry", call_args)

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_log_entry_delete(self, mock_logger):
        """Test before_delete hook (applies to all entities)"""
        self.plugin.log_entry_delete(
            entity_name="any_entity", user=self.mock_user, entry=self.mock_entry
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("Entry deleting", call_args)
        self.assertIn("test_entry", call_args)
        self.assertIn("any_entity", call_args)

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_log_entry_delete_different_entities(self, mock_logger):
        """Test that delete hook works for different entities"""
        for entity_name in ["entity1", "entity2", "helloworld"]:
            mock_logger.reset_mock()
            self.plugin.log_entry_delete(
                entity_name=entity_name, user=self.mock_user, entry=self.mock_entry
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            self.assertIn(entity_name, call_args)


class TestEntityHooks(unittest.TestCase):
    """Test cases for entity lifecycle hooks"""

    def setUp(self):
        """Set up test fixtures"""
        self.plugin = HelloWorldPlugin()
        self.mock_user = MagicMock()
        self.mock_user.username = "test_user"
        self.mock_entity = MagicMock()
        self.mock_entity.name = "test_entity"

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_log_entity_create(self, mock_logger):
        """Test after_create hook for entity"""
        self.plugin.log_entity_create(user=self.mock_user, entity=self.mock_entity)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("Entity created", call_args)
        self.assertIn("test_entity", call_args)
        self.assertIn("test_user", call_args)

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_log_entity_before_update(self, mock_logger):
        """Test before_update hook for entity"""
        validated_data = {"name": "updated_entity"}

        result = self.plugin.log_entity_before_update(
            user=self.mock_user, validated_data=validated_data, entity=self.mock_entity
        )

        # Check logging
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("Entity updating", call_args)
        self.assertIn("test_entity", call_args)

        # Check that validated_data is returned
        self.assertEqual(result, validated_data)

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_log_entity_after_update(self, mock_logger):
        """Test after_update hook for entity"""
        self.plugin.log_entity_after_update(user=self.mock_user, entity=self.mock_entity)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("Entity updated", call_args)
        self.assertIn("test_entity", call_args)


class TestValidationHook(unittest.TestCase):
    """Test cases for validation hook"""

    def setUp(self):
        """Set up test fixtures"""
        self.plugin = HelloWorldPlugin()
        self.mock_user = MagicMock()

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_validate_entry_valid_name(self, mock_logger):
        """Test validation with valid entry name"""
        # Should not raise any exception
        self.plugin.validate_entry(
            user=self.mock_user,
            schema_name="test_schema",
            name="valid_entry",
            attrs=[],
            instance=None,
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("Validating entry", call_args)
        self.assertIn("valid_entry", call_args)

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_validate_entry_forbidden_name_lowercase(self, mock_logger):
        """Test validation rejects 'forbidden' in name (lowercase)"""
        with self.assertRaises(ValueError) as context:
            self.plugin.validate_entry(
                user=self.mock_user,
                schema_name="test_schema",
                name="forbidden_entry",
                attrs=[],
                instance=None,
            )

        self.assertIn("forbidden", str(context.exception))
        self.assertIn("plugin rule", str(context.exception))

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_validate_entry_forbidden_name_uppercase(self, mock_logger):
        """Test validation rejects 'forbidden' in name (uppercase)"""
        with self.assertRaises(ValueError) as context:
            self.plugin.validate_entry(
                user=self.mock_user,
                schema_name="test_schema",
                name="FORBIDDEN_ENTRY",
                attrs=[],
                instance=None,
            )

        self.assertIn("forbidden", str(context.exception))

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_validate_entry_forbidden_name_mixed_case(self, mock_logger):
        """Test validation rejects 'forbidden' in name (mixed case)"""
        with self.assertRaises(ValueError) as context:
            self.plugin.validate_entry(
                user=self.mock_user,
                schema_name="test_schema",
                name="my_FoRbIdDeN_entry",
                attrs=[],
                instance=None,
            )

        self.assertIn("forbidden", str(context.exception))


class TestGetAttrsHooks(unittest.TestCase):
    """Test cases for get_attrs hooks"""

    def setUp(self):
        """Set up test fixtures"""
        self.plugin = HelloWorldPlugin()
        self.mock_entry = MagicMock()
        self.mock_entry.name = "test_entry"
        self.mock_entity = MagicMock()
        self.mock_entity.name = "test_entity"

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_get_entry_attrs(self, mock_logger):
        """Test get_attrs hook for entry"""
        attrinfo = [{"name": "attr1", "value": "value1"}]

        result = self.plugin.get_entry_attrs(
            entry=self.mock_entry, attrinfo=attrinfo, is_retrieve=True
        )

        # Check logging
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("Getting entry attrs", call_args)
        self.assertIn("test_entry", call_args)
        self.assertIn("True", call_args)

        # Check that attrinfo is returned unchanged
        self.assertEqual(result, attrinfo)

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_get_entry_attrs_not_retrieve(self, mock_logger):
        """Test get_attrs hook for entry when not in retrieve mode"""
        attrinfo = [{"name": "attr1", "value": "value1"}]

        result = self.plugin.get_entry_attrs(
            entry=self.mock_entry, attrinfo=attrinfo, is_retrieve=False
        )

        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("False", call_args)
        self.assertEqual(result, attrinfo)

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_get_entity_attrs(self, mock_logger):
        """Test get_attrs hook for entity"""
        attrinfo = [{"name": "entity_attr1", "type": "string"}]

        result = self.plugin.get_entity_attrs(entity=self.mock_entity, attrinfo=attrinfo)

        # Check logging
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("Getting entity attrs", call_args)
        self.assertIn("test_entity", call_args)

        # Check that attrinfo is returned unchanged
        self.assertEqual(result, attrinfo)

    @patch("pagoda_hello_world_plugin.plugin.logger")
    def test_get_entity_attrs_empty_list(self, mock_logger):
        """Test get_attrs hook for entity with empty attribute list"""
        attrinfo = []

        result = self.plugin.get_entity_attrs(entity=self.mock_entity, attrinfo=attrinfo)

        mock_logger.info.assert_called_once()
        self.assertEqual(result, attrinfo)


if __name__ == "__main__":
    unittest.main()
