from rest_framework.exceptions import ValidationError

from airone.lib.test import AironeViewTest
from airone.lib.types import AttrType
from entity.api_v2.serializers import EntityAttrCreateSerializer, EntityAttrUpdateSerializer
from entity.models import Entity, EntityAttr
from user.models import User


class EntityAttrSerializerTest(AironeViewTest):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="test_user")
        self.entity = Entity.objects.create(name="test_entity", created_user=self.user)

    def _get_serializer_context(self):
        """Helper method to provide proper context for serializers"""
        from unittest.mock import Mock

        mock_request = Mock()
        mock_request.user = self.user
        return {"request": mock_request}

    def test_create_attr_with_string_default_value(self):
        """Test creating string attribute with valid default values"""
        data = {"name": "string_attr", "type": AttrType.STRING, "default_value": "test default"}
        serializer = EntityAttrCreateSerializer(data=data, context=self._get_serializer_context())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["default_value"], "test default")

    def test_create_attr_with_text_default_value(self):
        """Test creating text attribute with valid default values"""
        data = {"name": "text_attr", "type": AttrType.TEXT, "default_value": "multi\nline\ntext"}
        serializer = EntityAttrCreateSerializer(data=data, context=self._get_serializer_context())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["default_value"], "multi\nline\ntext")

    def test_create_attr_with_boolean_default_value(self):
        """Test creating boolean attribute with valid default values"""
        # Test with actual boolean
        data = {"name": "bool_attr", "type": AttrType.BOOLEAN, "default_value": True}
        serializer = EntityAttrCreateSerializer(data=data, context=self._get_serializer_context())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["default_value"], True)

        # Test with boolean False
        data["default_value"] = False
        serializer = EntityAttrCreateSerializer(data=data, context=self._get_serializer_context())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["default_value"], False)

    def test_create_attr_boolean_string_conversion(self):
        """Test boolean attribute with string values should be rejected"""
        # All string values should be rejected for boolean type
        test_cases = [
            "true",
            "false",
            "True",
            "False",
            "TRUE",
            "FALSE",
            "1",
            "0",
        ]

        for input_value in test_cases:
            data = {"name": "bool_attr", "type": AttrType.BOOLEAN, "default_value": input_value}
            serializer = EntityAttrCreateSerializer(
                data=data, context=self._get_serializer_context()
            )
            with self.assertRaises(ValidationError, msg=f"Should fail for string: {input_value}"):
                serializer.is_valid(raise_exception=True)

    def test_create_attr_boolean_numeric_conversion(self):
        """Test boolean attribute with numeric values should be rejected"""
        # All numeric values should be rejected for boolean type
        test_cases = [
            1,
            0,
            1.0,
            0.0,
        ]

        for input_value in test_cases:
            data = {"name": "bool_attr", "type": AttrType.BOOLEAN, "default_value": input_value}
            serializer = EntityAttrCreateSerializer(
                data=data, context=self._get_serializer_context()
            )
            with self.assertRaises(ValidationError, msg=f"Should fail for number: {input_value}"):
                serializer.is_valid(raise_exception=True)

    def test_create_attr_invalid_boolean_values(self):
        """Test boolean attribute with invalid values that should raise ValidationError"""
        invalid_values = [
            "yes",
            "no",
            "on",
            "off",
            "invalid",
            "true",  # String values now rejected
            "false",
            "TRUE",
            "FALSE",
            "1",
            "0",
            1,  # Numeric values now rejected
            0,
            1.0,
            0.0,
            2,
            -1,
            1.5,
            [],
            {},
        ]

        for invalid_value in invalid_values:
            data = {"name": "bool_attr", "type": AttrType.BOOLEAN, "default_value": invalid_value}
            serializer = EntityAttrCreateSerializer(
                data=data, context=self._get_serializer_context()
            )
            with self.assertRaises(ValidationError, msg=f"Should fail for: {invalid_value}"):
                serializer.is_valid(raise_exception=True)

    def test_create_attr_invalid_string_values(self):
        """Test string attribute with invalid non-string values"""
        invalid_values = [
            123,
            True,
            [],
            {},
        ]

        for invalid_value in invalid_values:
            data = {"name": "string_attr", "type": AttrType.STRING, "default_value": invalid_value}
            serializer = EntityAttrCreateSerializer(
                data=data, context=self._get_serializer_context()
            )
            with self.assertRaises(ValidationError, msg=f"Should fail for: {invalid_value}"):
                serializer.is_valid(raise_exception=True)

    def test_create_attr_invalid_text_values(self):
        """Test text attribute with invalid non-string values"""
        invalid_values = [
            123,
            True,
            [],
            {},
        ]

        for invalid_value in invalid_values:
            data = {"name": "text_attr", "type": AttrType.TEXT, "default_value": invalid_value}
            serializer = EntityAttrCreateSerializer(
                data=data, context=self._get_serializer_context()
            )
            with self.assertRaises(ValidationError, msg=f"Should fail for: {invalid_value}"):
                serializer.is_valid(raise_exception=True)

    def test_create_attr_unsupported_type_clears_default_value(self):
        """Test that unsupported types clear the default_value"""
        # Create a reference entity for the OBJECT type
        ref_entity = Entity.objects.create(name="ref_entity", created_user=self.user)

        data = {
            "name": "object_attr",
            "type": AttrType.OBJECT,
            "default_value": "some value",
            "referral": [ref_entity.id],
        }
        serializer = EntityAttrCreateSerializer(data=data, context=self._get_serializer_context())
        # This should be valid but default_value should be cleared
        self.assertTrue(serializer.is_valid())
        self.assertIsNone(serializer.validated_data["default_value"])

    def test_update_attr_default_value(self):
        """Test updating attribute default values"""
        # Create an existing attribute
        attr = EntityAttr.objects.create(
            name="test_attr",
            type=AttrType.STRING,
            created_user=self.user,
            parent_entity=self.entity,
            default_value="original value",
        )

        # Test updating default value
        data = {"id": attr.id, "default_value": "updated value"}
        serializer = EntityAttrUpdateSerializer(data=data, context=self._get_serializer_context())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["default_value"], "updated value")

    def test_update_attr_boolean_conversion(self):
        """Test updating boolean attribute with string value should be rejected"""
        # Create an existing boolean attribute
        attr = EntityAttr.objects.create(
            name="bool_attr",
            type=AttrType.BOOLEAN,
            created_user=self.user,
            parent_entity=self.entity,
            default_value=False,
        )

        # Test updating with string value should fail
        data = {"id": attr.id, "default_value": "true"}
        serializer = EntityAttrUpdateSerializer(data=data, context=self._get_serializer_context())
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_update_attr_invalid_default_value(self):
        """Test updating attribute with invalid default value"""
        # Create an existing string attribute
        attr = EntityAttr.objects.create(
            name="string_attr",
            type=AttrType.STRING,
            created_user=self.user,
            parent_entity=self.entity,
        )

        # Test updating with invalid value
        data = {
            "id": attr.id,
            "default_value": 123,  # Invalid for string type
        }
        serializer = EntityAttrUpdateSerializer(data=data, context=self._get_serializer_context())
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_attr_null_default_value(self):
        """Test that None/null default values are handled correctly"""
        for attr_type in [AttrType.STRING, AttrType.TEXT, AttrType.BOOLEAN]:
            data = {"name": f"attr_{attr_type}", "type": attr_type, "default_value": None}
            serializer = EntityAttrCreateSerializer(
                data=data, context=self._get_serializer_context()
            )
            self.assertTrue(serializer.is_valid(), f"Failed for type: {attr_type}")
            self.assertIsNone(serializer.validated_data["default_value"])

    def test_update_attr_existing_type_inference(self):
        """Test update serializer infers type from existing attribute when type is not provided"""
        # Create an existing boolean attribute
        attr = EntityAttr.objects.create(
            name="bool_attr",
            type=AttrType.BOOLEAN,
            created_user=self.user,
            parent_entity=self.entity,
        )

        # Update without specifying type - string values should be rejected
        data = {
            "id": attr.id,
            "default_value": "true",  # String should be rejected for boolean type
        }
        serializer = EntityAttrUpdateSerializer(data=data, context=self._get_serializer_context())
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

        # Test with valid boolean value
        data["default_value"] = True
        serializer = EntityAttrUpdateSerializer(data=data, context=self._get_serializer_context())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["default_value"], True)
