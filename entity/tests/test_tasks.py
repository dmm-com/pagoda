from django.test import TestCase
from pydantic import ValidationError

from airone.lib.types import AttrType
from entity.tasks import (
    CreateEntityAttr,
    CreateEntityParams,
    CreateEntityV2Attr,
    CreateEntityV2Params,
    CreateEntityV2Webhook,
    EditEntityAttr,
    EditEntityV2Attr,
    EditEntityV2Params,
    EditEntityV2Webhook,
    WebhookHeader,
)


class CreateEntityAttrTest(TestCase):
    """Tests for CreateEntityAttr Pydantic model."""

    def test_valid_attr_with_int_type(self):
        """Test creating a valid attribute with integer type."""
        attr = CreateEntityAttr(
            name="test_attr",
            type=AttrType.STRING,
            is_mandatory=True,
            is_delete_in_chain=False,
            row_index="1",
            ref_ids=[],
        )
        self.assertEqual(attr.name, "test_attr")
        self.assertEqual(attr.type, AttrType.STRING)
        self.assertEqual(attr.is_mandatory, True)

    def test_valid_attr_with_string_type(self):
        """Test creating a valid attribute with string type (converted to int)."""
        attr = CreateEntityAttr(
            name="test_attr",
            type="2",  # STRING as string
            is_mandatory=True,
            is_delete_in_chain=False,
            row_index="1",
            ref_ids=[],
        )
        self.assertEqual(attr.type, 2)

    def test_invalid_string_type(self):
        """Test that invalid string type raises ValidationError."""
        with self.assertRaises(ValidationError) as context:
            CreateEntityAttr(
                name="test_attr",
                type="invalid",
                is_mandatory=True,
                is_delete_in_chain=False,
                row_index="1",
            )
        self.assertIn("Invalid type value", str(context.exception))

    def test_name_max_length_validation(self):
        """Test that name exceeding max length raises ValidationError."""
        with self.assertRaises(ValidationError):
            CreateEntityAttr(
                name="x" * 201,  # Exceeds max_length=200
                type=AttrType.STRING,
                is_mandatory=True,
                is_delete_in_chain=False,
                row_index="1",
            )


class CreateEntityParamsTest(TestCase):
    """Tests for CreateEntityParams Pydantic model."""

    def test_valid_params(self):
        """Test creating valid entity params."""
        params = CreateEntityParams(
            attrs=[
                {
                    "name": "attr1",
                    "type": AttrType.STRING,
                    "is_mandatory": True,
                    "is_delete_in_chain": False,
                    "row_index": "1",
                    "ref_ids": [],
                }
            ]
        )
        self.assertEqual(len(params.attrs), 1)
        self.assertEqual(params.attrs[0].name, "attr1")

    def test_empty_attrs(self):
        """Test that empty attrs list is valid."""
        params = CreateEntityParams(attrs=[])
        self.assertEqual(len(params.attrs), 0)


class EditEntityAttrTest(TestCase):
    """Tests for EditEntityAttr Pydantic model."""

    def test_valid_attr_with_id(self):
        """Test creating a valid attribute with id (for editing)."""
        attr = EditEntityAttr(
            id=123,
            name="test_attr",
            type=AttrType.STRING,
            is_mandatory=True,
            is_delete_in_chain=False,
            row_index="1",
            ref_ids=[],
        )
        self.assertEqual(attr.id, 123)
        self.assertEqual(attr.name, "test_attr")

    def test_valid_attr_without_id(self):
        """Test creating a valid attribute without id (for new attr)."""
        attr = EditEntityAttr(
            name="test_attr",
            type=AttrType.STRING,
            is_mandatory=True,
            is_delete_in_chain=False,
            row_index="1",
        )
        self.assertIsNone(attr.id)

    def test_deleted_flag(self):
        """Test that deleted flag works correctly."""
        attr = EditEntityAttr(
            id=123,
            name="test_attr",
            type=AttrType.STRING,
            is_mandatory=True,
            is_delete_in_chain=False,
            row_index="1",
            deleted=True,
        )
        self.assertEqual(attr.deleted, True)


class WebhookHeaderTest(TestCase):
    """Tests for WebhookHeader Pydantic model."""

    def test_valid_header(self):
        """Test creating a valid webhook header."""
        header = WebhookHeader(header_key="Authorization", header_value="Bearer token123")
        self.assertEqual(header.header_key, "Authorization")
        self.assertEqual(header.header_value, "Bearer token123")

    def test_missing_fields(self):
        """Test that missing required fields raise ValidationError."""
        with self.assertRaises(ValidationError):
            WebhookHeader(header_key="Authorization")


class CreateEntityV2WebhookTest(TestCase):
    """Tests for CreateEntityV2Webhook Pydantic model."""

    def test_valid_webhook_with_defaults(self):
        """Test creating a webhook with default values."""
        webhook = CreateEntityV2Webhook(url="http://example.com")
        self.assertEqual(webhook.url, "http://example.com")
        self.assertEqual(webhook.label, "")
        self.assertEqual(webhook.is_enabled, False)
        self.assertEqual(len(webhook.headers), 0)

    def test_valid_webhook_with_all_fields(self):
        """Test creating a webhook with all fields."""
        webhook = CreateEntityV2Webhook(
            url="http://example.com",
            label="test webhook",
            is_enabled=True,
            headers=[
                {"header_key": "Authorization", "header_value": "Bearer token123"},
            ],
        )
        self.assertEqual(webhook.label, "test webhook")
        self.assertEqual(webhook.is_enabled, True)
        self.assertEqual(len(webhook.headers), 1)

    def test_url_max_length_validation(self):
        """Test that URL exceeding max length raises ValidationError."""
        with self.assertRaises(ValidationError):
            CreateEntityV2Webhook(url="x" * 201)

    def test_webhook_without_url_uses_default(self):
        """Test that webhook without URL uses default empty string."""
        webhook = CreateEntityV2Webhook()
        self.assertEqual(webhook.url, "")


class EditEntityV2WebhookTest(TestCase):
    """Tests for EditEntityV2Webhook Pydantic model."""

    def test_valid_webhook_with_id(self):
        """Test creating a webhook with id (for editing)."""
        webhook = EditEntityV2Webhook(
            id=123, url="http://example.com", label="test", is_enabled=True
        )
        self.assertEqual(webhook.id, 123)
        self.assertEqual(webhook.url, "http://example.com")

    def test_valid_webhook_without_id(self):
        """Test creating a webhook without id (for new webhook)."""
        webhook = EditEntityV2Webhook(url="http://example.com")
        self.assertIsNone(webhook.id)

    def test_is_deleted_flag(self):
        """Test that is_deleted flag works correctly."""
        webhook = EditEntityV2Webhook(id=123, is_deleted=True)
        self.assertEqual(webhook.is_deleted, True)

    def test_all_fields_optional_except_defaults(self):
        """Test that all fields are optional (have defaults)."""
        webhook = EditEntityV2Webhook()
        self.assertIsNone(webhook.id)
        self.assertIsNone(webhook.url)
        self.assertEqual(webhook.label, "")
        self.assertEqual(webhook.is_enabled, False)
        self.assertEqual(webhook.is_deleted, False)


class CreateEntityV2AttrTest(TestCase):
    """Tests for CreateEntityV2Attr Pydantic model."""

    def test_valid_attr_with_defaults(self):
        """Test creating a valid attribute with default values."""
        attr = CreateEntityV2Attr(name="test_attr", type=AttrType.STRING)
        self.assertEqual(attr.name, "test_attr")
        self.assertEqual(attr.type, AttrType.STRING)
        self.assertEqual(attr.is_mandatory, False)
        self.assertEqual(attr.is_delete_in_chain, False)
        self.assertEqual(attr.is_summarized, False)
        self.assertEqual(len(attr.referral), 0)
        self.assertEqual(attr.note, "")

    def test_valid_attr_with_all_fields(self):
        """Test creating a valid attribute with all fields."""
        attr = CreateEntityV2Attr(
            name="test_attr",
            type=AttrType.STRING,
            index=1,
            is_mandatory=True,
            is_delete_in_chain=True,
            is_summarized=True,
            referral=[1, 2, 3],
            note="test note",
            default_value="test default",
        )
        self.assertEqual(attr.is_mandatory, True)
        self.assertEqual(attr.default_value, "test default")

    def test_default_value_for_string_type(self):
        """Test that default_value works for STRING type."""
        attr = CreateEntityV2Attr(name="test_attr", type=AttrType.STRING, default_value="test")
        self.assertEqual(attr.default_value, "test")

    def test_default_value_for_text_type(self):
        """Test that default_value works for TEXT type."""
        attr = CreateEntityV2Attr(name="test_attr", type=AttrType.TEXT, default_value="test")
        self.assertEqual(attr.default_value, "test")

    def test_default_value_for_boolean_type(self):
        """Test that default_value works for BOOLEAN type."""
        attr = CreateEntityV2Attr(name="test_attr", type=AttrType.BOOLEAN, default_value=True)
        self.assertEqual(attr.default_value, True)

    def test_default_value_for_number_type(self):
        """Test that default_value works for NUMBER type."""
        attr = CreateEntityV2Attr(name="test_attr", type=AttrType.NUMBER, default_value=42)
        self.assertEqual(attr.default_value, 42)

        attr = CreateEntityV2Attr(name="test_attr", type=AttrType.NUMBER, default_value=3.14)
        self.assertEqual(attr.default_value, 3.14)

    def test_default_value_cleared_for_unsupported_type(self):
        """Test that default_value is cleared for unsupported types (e.g., OBJECT)."""
        # This should log a warning but not raise an error
        attr = CreateEntityV2Attr(name="test_attr", type=AttrType.OBJECT, default_value="test")
        self.assertIsNone(attr.default_value)

    def test_default_value_type_mismatch_for_string(self):
        """Test that default_value is cleared when type mismatches (STRING)."""
        attr = CreateEntityV2Attr(name="test_attr", type=AttrType.STRING, default_value=123)
        self.assertIsNone(attr.default_value)

    def test_default_value_type_mismatch_for_boolean(self):
        """Test that default_value is cleared when type mismatches (BOOLEAN)."""
        attr = CreateEntityV2Attr(name="test_attr", type=AttrType.BOOLEAN, default_value="true")
        self.assertIsNone(attr.default_value)

    def test_default_value_type_mismatch_for_number(self):
        """Test that default_value is cleared when type mismatches (NUMBER)."""
        attr = CreateEntityV2Attr(name="test_attr", type=AttrType.NUMBER, default_value="42")
        self.assertIsNone(attr.default_value)

    def test_name_max_length_validation(self):
        """Test that name exceeding max length raises ValidationError."""
        with self.assertRaises(ValidationError):
            CreateEntityV2Attr(name="x" * 201, type=AttrType.STRING)


class CreateEntityV2ParamsTest(TestCase):
    """Tests for CreateEntityV2Params Pydantic model."""

    def test_valid_params_with_name_only(self):
        """Test creating valid params with name only."""
        params = CreateEntityV2Params(name="test_entity")
        self.assertEqual(params.name, "test_entity")
        self.assertEqual(params.note, "")
        self.assertEqual(len(params.attrs), 0)
        self.assertEqual(len(params.webhooks), 0)

    def test_valid_params_with_all_fields(self):
        """Test creating valid params with all fields."""
        params = CreateEntityV2Params(
            name="test_entity",
            note="test note",
            attrs=[{"name": "attr1", "type": AttrType.STRING}],
            webhooks=[{"url": "http://example.com"}],
        )
        self.assertEqual(params.name, "test_entity")
        self.assertEqual(params.note, "test note")
        self.assertEqual(len(params.attrs), 1)
        self.assertEqual(len(params.webhooks), 1)

    def test_name_max_length_validation(self):
        """Test that name exceeding max length raises ValidationError."""
        with self.assertRaises(ValidationError):
            CreateEntityV2Params(name="x" * 201)


class EditEntityV2AttrTest(TestCase):
    """Tests for EditEntityV2Attr Pydantic model."""

    def test_valid_attr_with_id_has_optional_fields(self):
        """Test that existing attrs (with id) can have optional fields."""
        # When id is provided, name and type are not required
        attr = EditEntityV2Attr(id=123)
        self.assertEqual(attr.id, 123)
        self.assertIsNone(attr.name)
        self.assertIsNone(attr.type)
        self.assertEqual(attr.is_deleted, False)

    def test_new_attr_requires_name_and_type(self):
        """Test that new attrs (without id) require name and type."""
        with self.assertRaises(ValidationError) as context:
            EditEntityV2Attr()
        self.assertIn("name and type are required", str(context.exception))

    def test_valid_attr_with_some_fields(self):
        """Test creating an attr with some fields."""
        attr = EditEntityV2Attr(id=123, name="updated_attr", type=AttrType.TEXT)
        self.assertEqual(attr.id, 123)
        self.assertEqual(attr.name, "updated_attr")
        self.assertEqual(attr.type, AttrType.TEXT)

    def test_is_deleted_flag(self):
        """Test that is_deleted flag works correctly."""
        attr = EditEntityV2Attr(id=123, is_deleted=True)
        self.assertEqual(attr.is_deleted, True)

    def test_name_max_length_validation(self):
        """Test that name exceeding max length raises ValidationError."""
        with self.assertRaises(ValidationError):
            EditEntityV2Attr(name="x" * 201)


class EditEntityV2ParamsTest(TestCase):
    """Tests for EditEntityV2Params Pydantic model."""

    def test_valid_params_with_name_only(self):
        """Test creating valid params with name only."""
        params = EditEntityV2Params(name="updated_entity")
        self.assertEqual(params.name, "updated_entity")

    def test_valid_params_with_all_fields(self):
        """Test creating valid params with all fields."""
        params = EditEntityV2Params(
            name="updated_entity",
            note="updated note",
            is_toplevel=True,
            attrs=[{"id": 123, "name": "updated_attr"}],
            webhooks=[{"id": 456, "url": "http://example.com"}],
        )
        self.assertEqual(params.name, "updated_entity")
        self.assertEqual(params.note, "updated note")
        self.assertEqual(params.is_toplevel, True)
        self.assertEqual(len(params.attrs), 1)
        self.assertEqual(len(params.webhooks), 1)

    def test_all_fields_optional(self):
        """Test that all fields are optional."""
        params = EditEntityV2Params()
        self.assertIsNone(params.name)
        self.assertIsNone(params.note)
        self.assertIsNone(params.is_toplevel)
        self.assertEqual(len(params.attrs), 0)
        self.assertEqual(len(params.webhooks), 0)

    def test_name_max_length_validation(self):
        """Test that name exceeding max length raises ValidationError."""
        with self.assertRaises(ValidationError):
            EditEntityV2Params(name="x" * 201)
