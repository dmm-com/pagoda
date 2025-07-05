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

    def test_create_attr_with_number_default_value(self):
        """Test creating number attribute with valid default values"""
        # Test with integer
        data = {"name": "number_attr", "type": AttrType.NUMBER, "default_value": 42}
        serializer = EntityAttrCreateSerializer(data=data, context=self._get_serializer_context())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["default_value"], 42)

        # Test with float
        data["default_value"] = 3.14
        serializer = EntityAttrCreateSerializer(data=data, context=self._get_serializer_context())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["default_value"], 3.14)

        # Test with negative number
        data["default_value"] = -123.45
        serializer = EntityAttrCreateSerializer(data=data, context=self._get_serializer_context())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["default_value"], -123.45)

        # Test with zero
        data["default_value"] = 0
        serializer = EntityAttrCreateSerializer(data=data, context=self._get_serializer_context())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["default_value"], 0)

        # Test with zero float
        data["default_value"] = 0.0
        serializer = EntityAttrCreateSerializer(data=data, context=self._get_serializer_context())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["default_value"], 0.0)

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

    def test_create_attr_invalid_number_values(self):
        """Test number attribute with invalid values that should raise ValidationError"""
        import math
        
        invalid_values = [
            "123",  # String numbers should be rejected
            "3.14",
            "-42",
            "0",
            "text",  # Non-numeric strings
            "abc",
            True,  # Boolean values
            False,
            [],  # Lists and other types
            {},
            None,  # None should be handled separately
            math.nan,  # NaN should be rejected
            math.inf,  # Infinity should be rejected
            -math.inf,  # Negative infinity should be rejected
        ]

        for invalid_value in invalid_values:
            data = {"name": "number_attr", "type": AttrType.NUMBER, "default_value": invalid_value}
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
        for attr_type in [AttrType.STRING, AttrType.TEXT, AttrType.BOOLEAN, AttrType.NUMBER]:
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

    def test_update_attr_number_default_value(self):
        """Test updating number attribute with valid default values"""
        # Create an existing number attribute
        attr = EntityAttr.objects.create(
            name="number_attr",
            type=AttrType.NUMBER,
            created_user=self.user,
            parent_entity=self.entity,
            default_value=42,
        )

        # Test updating with valid integer
        data = {"id": attr.id, "default_value": 100}
        serializer = EntityAttrUpdateSerializer(data=data, context=self._get_serializer_context())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["default_value"], 100)

        # Test updating with valid float
        data["default_value"] = 3.14159
        serializer = EntityAttrUpdateSerializer(data=data, context=self._get_serializer_context())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["default_value"], 3.14159)

    def test_update_attr_invalid_number_values(self):
        """Test updating number attribute with invalid values"""
        import math
        
        # Create an existing number attribute
        attr = EntityAttr.objects.create(
            name="number_attr",
            type=AttrType.NUMBER,
            created_user=self.user,
            parent_entity=self.entity,
            default_value=42,
        )

        # Test invalid values
        invalid_values = [
            "123",  # String should be rejected
            "not_a_number",
            True,  # Boolean should be rejected
            False,
            [],  # Other types should be rejected
            {},
            math.nan,  # NaN should be rejected
            math.inf,  # Infinity should be rejected
            -math.inf,  # Negative infinity should be rejected
        ]

        for invalid_value in invalid_values:
            data = {"id": attr.id, "default_value": invalid_value}
            serializer = EntityAttrUpdateSerializer(
                data=data, context=self._get_serializer_context()
            )
            with self.assertRaises(ValidationError, msg=f"Should fail for: {invalid_value}"):
                serializer.is_valid(raise_exception=True)
