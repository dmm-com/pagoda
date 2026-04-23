import json
import math
from unittest import mock
from unittest.mock import Mock, patch

import yaml
from rest_framework import status

from airone.lib.elasticsearch import EntryFilterKey, FilterKey
from airone.lib.types import (
    AttrType,
)
from entity.models import ItemNameType
from entry import tasks
from entry.models import Entry
from entry.tests.test_api_v2 import BaseViewTest
from job.models import Job, JobOperation, JobStatus


class ViewTest(BaseViewTest):
    def _create_lb_models_for_autoname(self):
        """
        This is a helper function to create LB and LBServiceGroup models for autoname tests.
        """
        model_lb = self.create_entity(self.user, "LB")
        model_sg = self.create_entity(
            self.user,
            "LBServiceGroup",
            attrs=[
                {
                    "name": "LB",
                    "type": AttrType.OBJECT,
                    "ref": model_lb,
                    "name_order": 1,
                    "name_prefix": "[",
                    "name_postfix": "]",
                },
                {"name": "label", "type": AttrType.STRING},
                {"name": "domain", "type": AttrType.STRING, "name_order": 2, "name_prefix": " "},
                {"name": "port", "type": AttrType.STRING, "name_order": 3, "name_prefix": ":"},
                {
                    "name": "number",
                    "type": AttrType.NUMBER,
                    "name_order": 4,
                    "name_prefix": " #",
                },
                {
                    "name": "dict",
                    "type": AttrType.NAMED_OBJECT,
                    "name_order": 5,
                },  # This should be ignored
            ],
            item_name_type=ItemNameType.ATTR,
        )

        return (model_lb, model_sg)

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=tasks.create_entry_v2))
    def test_create_entry_with_default_values(self):
        """Test entries are created with default values from EntityAttr when no value provided"""
        # Create entity with attributes that have default values
        entity = self.create_entity(
            self.user,
            "TestEntity",
            attrs=[
                {"name": "string_with_default", "type": AttrType.STRING},
                {"name": "bool_with_default", "type": AttrType.BOOLEAN},
                {"name": "text_with_default", "type": AttrType.TEXT},
                {"name": "number_with_default", "type": AttrType.NUMBER},
                {"name": "string_no_default", "type": AttrType.STRING},
            ],
        )

        # Set default values for some attributes
        string_attr = entity.attrs.get(name="string_with_default")
        string_attr.default_value = "default string value"
        string_attr.save()

        bool_attr = entity.attrs.get(name="bool_with_default")
        bool_attr.default_value = True
        bool_attr.save()

        text_attr = entity.attrs.get(name="text_with_default")
        text_attr.default_value = "default text value"
        text_attr.save()

        number_attr = entity.attrs.get(name="number_with_default")
        number_attr.default_value = 42.5
        number_attr.save()

        # Create entry without providing values for attributes with defaults
        params = {
            "name": "test_entry",
            "attrs": [
                # Only provide value for one attribute, others should use defaults
                {"id": entity.attrs.get(name="string_no_default").id, "value": "provided value"}
            ],
        }

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Wait for entry creation job to complete
        job = Job.objects.filter(operation=JobOperation.CREATE_ENTRY_V2).last()
        self.assertEqual(job.status, JobStatus.DONE)

        # Verify entry was created with default values
        entry = Entry.objects.get(name="test_entry", schema=entity)
        self.assertIsNotNone(entry)

        # Check that attributes with default values were created with those defaults
        string_attr_value = entry.attrs.get(schema=string_attr)
        self.assertEqual(string_attr_value.get_latest_value().get_value(), "default string value")

        bool_attr_value = entry.attrs.get(schema=bool_attr)
        self.assertEqual(bool_attr_value.get_latest_value().get_value(), True)

        text_attr_value = entry.attrs.get(schema=text_attr)
        self.assertEqual(text_attr_value.get_latest_value().get_value(), "default text value")

        number_attr_value = entry.attrs.get(schema=number_attr)
        self.assertEqual(number_attr_value.get_latest_value().get_value(), 42.5)

        # Check that attribute without default was not created (no value provided)
        string_no_default_attr = entity.attrs.get(name="string_no_default")
        string_no_default_value = entry.attrs.get(schema=string_no_default_attr)
        self.assertEqual(string_no_default_value.get_latest_value().get_value(), "provided value")

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=tasks.create_entry_v2))
    def test_create_entry_provided_value_overrides_default(self):
        """Test that provided values override default values from EntityAttr"""
        # Create entity with attribute that has default value
        entity = self.create_entity(
            self.user,
            "TestEntity",
            attrs=[
                {"name": "string_attr", "type": AttrType.STRING},
                {"name": "bool_attr", "type": AttrType.BOOLEAN},
                {"name": "number_attr", "type": AttrType.NUMBER},
            ],
        )

        # Set default values
        string_attr = entity.attrs.get(name="string_attr")
        string_attr.default_value = "default value"
        string_attr.save()

        bool_attr = entity.attrs.get(name="bool_attr")
        bool_attr.default_value = True
        bool_attr.save()

        number_attr = entity.attrs.get(name="number_attr")
        number_attr.default_value = 123.456
        number_attr.save()

        # Create entry providing values that should override defaults
        params = {
            "name": "test_entry_override",
            "attrs": [
                {"id": string_attr.id, "value": "provided value"},
                {"id": bool_attr.id, "value": False},
                {"id": number_attr.id, "value": 999.999},
            ],
        }

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Wait for entry creation job to complete
        job = Job.objects.filter(operation=JobOperation.CREATE_ENTRY_V2).last()
        self.assertEqual(job.status, JobStatus.DONE)

        # Verify entry was created with provided values, not defaults
        entry = Entry.objects.get(name="test_entry_override", schema=entity)

        string_attr_value = entry.attrs.get(schema=string_attr)
        self.assertEqual(
            string_attr_value.get_latest_value().get_value(), "provided value"
        )  # Not default

        bool_attr_value = entry.attrs.get(schema=bool_attr)
        self.assertEqual(
            bool_attr_value.get_latest_value().get_value(), False
        )  # Not default (True)

        number_attr_value = entry.attrs.get(schema=number_attr)
        self.assertEqual(
            number_attr_value.get_latest_value().get_value(), 999.999
        )  # Not default (123.456)

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=tasks.create_entry_v2))
    def test_create_entry_unsupported_type_no_default(self):
        """Test that unsupported types don't get default values applied"""
        # Create reference entity
        ref_entity = self.create_entity(self.user, "RefEntity", attrs=[])

        # Create entity with unsupported type attribute that has default_value
        entity = self.create_entity(
            self.user,
            "TestEntity",
            attrs=[
                {"name": "object_attr", "type": AttrType.OBJECT, "referral": [ref_entity]},
                {"name": "date_attr", "type": AttrType.DATE},
            ],
        )

        # Try to set default values (should be ignored for unsupported types)
        object_attr = entity.attrs.get(name="object_attr")
        object_attr.default_value = "ignored value"
        object_attr.save()

        date_attr = entity.attrs.get(name="date_attr")
        date_attr.default_value = "2023-01-01"
        date_attr.save()

        # Create entry without providing values
        params = {
            "name": "test_entry_unsupported",
            "attrs": [],
        }

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Wait for entry creation job to complete
        job = Job.objects.filter(operation=JobOperation.CREATE_ENTRY_V2).last()
        self.assertEqual(job.status, JobStatus.DONE)

        # Verify entry was created but unsupported types should use type defaults, not custom
        entry = Entry.objects.get(name="test_entry_unsupported", schema=entity)

        # Since unsupported types don't apply default_value, these attributes should either
        # not have AttributeValues created or use the hardcoded type defaults
        object_attr_values = entry.attrs.filter(schema=object_attr)
        date_attr_values = entry.attrs.filter(schema=date_attr)

        # For unsupported types, no custom default should be applied
        # The behavior should be the same as before (either no value or type default)
        if object_attr_values.exists():
            object_attr_value = object_attr_values.first()
            # Should not be the custom default "ignored value"
            self.assertNotEqual(object_attr_value.get_latest_value().get_value(), "ignored value")

        if date_attr_values.exists():
            date_attr_value = date_attr_values.first()
            # Should not be the custom default "2023-01-01"
            self.assertNotEqual(date_attr_value.get_latest_value().get_value(), "2023-01-01")

    @mock.patch("entry.tasks.create_entry_v2.delay", mock.Mock(side_effect=tasks.create_entry_v2))
    def test_create_entry_number_default_value_scenarios(self):
        """Test Number type default value scenarios (integer, float, zero, negative)"""
        # Create entity with number attributes
        entity = self.create_entity(
            self.user,
            "NumberTestEntity",
            attrs=[
                {"name": "number_int", "type": AttrType.NUMBER},
                {"name": "number_float", "type": AttrType.NUMBER},
                {"name": "number_zero", "type": AttrType.NUMBER},
                {"name": "number_negative", "type": AttrType.NUMBER},
            ],
        )

        # Set different number default values
        number_int_attr = entity.attrs.get(name="number_int")
        number_int_attr.default_value = 42
        number_int_attr.save()

        number_float_attr = entity.attrs.get(name="number_float")
        number_float_attr.default_value = 3.14159
        number_float_attr.save()

        number_zero_attr = entity.attrs.get(name="number_zero")
        number_zero_attr.default_value = 0
        number_zero_attr.save()

        number_negative_attr = entity.attrs.get(name="number_negative")
        number_negative_attr.default_value = -123.45
        number_negative_attr.save()

        # Create entry without providing values for number attributes
        params = {
            "name": "test_entry_number_defaults",
            "attrs": [],
        }

        resp = self.client.post(
            "/entity/api/v2/%s/entries/" % entity.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Wait for entry creation job to complete
        job = Job.objects.filter(operation=JobOperation.CREATE_ENTRY_V2).last()
        self.assertEqual(job.status, JobStatus.DONE)

        # Verify entry was created with number default values
        entry = Entry.objects.get(name="test_entry_number_defaults", schema=entity)
        self.assertIsNotNone(entry)

        # Check integer default
        number_int_value = entry.attrs.get(schema=number_int_attr)
        self.assertEqual(number_int_value.get_latest_value().get_value(), 42)

        # Check float default
        number_float_value = entry.attrs.get(schema=number_float_attr)
        self.assertAlmostEqual(number_float_value.get_latest_value().get_value(), 3.14159, places=5)

        # Check zero default
        number_zero_value = entry.attrs.get(schema=number_zero_attr)
        self.assertEqual(number_zero_value.get_latest_value().get_value(), 0)

        # Check negative default
        number_negative_value = entry.attrs.get(schema=number_negative_attr)
        self.assertEqual(number_negative_value.get_latest_value().get_value(), -123.45)

    @patch("entry.tasks.create_entry_v2.delay", Mock(side_effect=tasks.create_entry_v2))
    def test_create_and_retrieve_entry_with_number_attr(self):
        entry_name = "test_entry_with_number"
        number_value = 123.45
        # Ensure 'num' attribute exists in self.entity, created via
        # ALL_TYPED_ATTR_PARAMS_FOR_CREATING_ENTITY
        num_entity_attr = self.entity.attrs.get(name="num")

        payload = {
            "name": entry_name,
            "schema": self.entity.id,
            "attrs": [{"id": num_entity_attr.id, "value": number_value}],
        }

        # Create Entry with Number attribute
        resp_create = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload, "application/json"
        )
        self.assertEqual(resp_create.status_code, status.HTTP_202_ACCEPTED, resp_create.content)

        # Wait for job to complete and get the created entry
        created_entry = Entry.objects.filter(name=entry_name, schema=self.entity).first()
        self.assertIsNotNone(created_entry, "Entry was not created")
        created_entry_id = created_entry.id

        # Retrieve the created entry
        resp_get = self.client.get(f"/entry/api/v2/{created_entry_id}/")
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK, resp_get.content)
        retrieved_data = resp_get.json()
        self.assertEqual(retrieved_data["name"], entry_name)

        # Check 'num' attribute in retrieval response
        num_attr_retrieved = None
        for attr in retrieved_data.get("attrs", []):
            if attr["schema"]["name"] == "num":
                num_attr_retrieved = attr
                break
        self.assertIsNotNone(num_attr_retrieved, "'num' attribute not found in retrieval response")
        # Verify the value of the 'num' attribute - check for as_number format
        self.assertAlmostEqual(num_attr_retrieved["value"]["as_number"], number_value, places=5)

        # Test with None value for number
        entry_name_none = "test_entry_with_number_none"
        payload_none = {
            "name": entry_name_none,
            "schema": self.entity.id,
            "attrs": [{"id": num_entity_attr.id, "value": None}],
        }
        resp_create_none = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload_none, "application/json"
        )
        self.assertEqual(
            resp_create_none.status_code, status.HTTP_202_ACCEPTED, resp_create_none.content
        )

        # Wait for job to complete and get the created entry
        created_entry_none = Entry.objects.filter(name=entry_name_none, schema=self.entity).first()
        self.assertIsNotNone(created_entry_none, "Entry with None value was not created")
        created_entry_id_none = created_entry_none.id

        resp_get_none = self.client.get(f"/entry/api/v2/{created_entry_id_none}/")
        self.assertEqual(resp_get_none.status_code, status.HTTP_200_OK, resp_get_none.content)
        retrieved_data_none = resp_get_none.json()
        num_attr_retrieved_none = None
        for attr in retrieved_data_none.get("attrs", []):
            if attr["schema"]["name"] == "num":
                num_attr_retrieved_none = attr
                break
        self.assertIsNotNone(num_attr_retrieved_none)
        self.assertIsNone(num_attr_retrieved_none["value"]["as_number"])

        # Test with invalid number value
        entry_name_invalid = "test_entry_with_invalid_number"
        payload_invalid = {
            "name": entry_name_invalid,
            "schema": self.entity.id,
            "attrs": [
                {
                    "id": num_entity_attr.id,
                    "value": "not-a-number",  # Invalid string for number
                }
            ],
        }
        resp_create_invalid = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload_invalid, "application/json"
        )
        self.assertEqual(
            resp_create_invalid.status_code,
            status.HTTP_400_BAD_REQUEST,
            resp_create_invalid.content,
        )

    @patch("entry.tasks.create_entry_v2.delay", Mock(side_effect=tasks.create_entry_v2))
    def test_create_and_retrieve_entry_with_array_number_attr(self):
        """Test array number functionality including creation, retrieval, and validation"""
        entry_name = "test_entry_with_array_number"
        number_values = [123.45, 67.89, 0.123, -45.67]

        # Ensure 'nums' attribute exists in self.entity
        nums_entity_attr = self.entity.attrs.get(name="nums")

        payload = {
            "name": entry_name,
            "schema": self.entity.id,
            "attrs": [{"id": nums_entity_attr.id, "value": number_values}],
        }

        # Create Entry with Array Number attribute
        resp_create = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload, "application/json"
        )
        self.assertEqual(resp_create.status_code, status.HTTP_202_ACCEPTED, resp_create.content)

        # Wait for job to complete and get the created entry
        created_entry = Entry.objects.filter(name=entry_name, schema=self.entity).first()
        self.assertIsNotNone(created_entry, "Entry was not created")
        created_entry_id = created_entry.id

        # Retrieve the created entry
        resp_get = self.client.get(f"/entry/api/v2/{created_entry_id}/")
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK, resp_get.content)
        retrieved_data = resp_get.json()
        self.assertEqual(retrieved_data["name"], entry_name)

        # Check 'nums' attribute in retrieval response
        nums_attr_retrieved = None
        for attr in retrieved_data.get("attrs", []):
            if attr["schema"]["name"] == "nums":
                nums_attr_retrieved = attr
                break
        self.assertIsNotNone(
            nums_attr_retrieved, "'nums' attribute not found in retrieval response"
        )

        # Verify the values of the 'nums' attribute - check for as_array_number format
        retrieved_values = nums_attr_retrieved["value"]["as_array_number"]
        self.assertEqual(len(retrieved_values), len(number_values))
        for i, expected_val in enumerate(number_values):
            self.assertAlmostEqual(retrieved_values[i], expected_val, places=5)

    @patch("entry.tasks.create_entry_v2.delay", Mock(side_effect=tasks.create_entry_v2))
    def test_create_for_autoname_item(self):
        (model_lb, model_sg) = self._create_lb_models_for_autoname()

        item_lb = self.add_entry(self.user, "LB0001", model_lb)
        payload = {
            "name": "ChangingName",
            "schema": model_sg.id,
            "attrs": [
                {"id": model_sg.attrs.get(name="LB").id, "value": item_lb.id},
                {"id": model_sg.attrs.get(name="label").id, "value": "This is test ServiceGroup"},
                {"id": model_sg.attrs.get(name="domain").id, "value": "test.example.com"},
                {"id": model_sg.attrs.get(name="port").id, "value": "8080"},
                {"id": model_sg.attrs.get(name="number").id, "value": 123.456},
                {
                    "id": model_sg.attrs.get(name="dict").id,
                    "value": {"id": item_lb.id, "name": "hoge"},
                },
            ],
        }

        # Create Entry with Array Number attribute
        resp_create = self.client.post(
            f"/entity/api/v2/{model_sg.id}/entries/", payload, "application/json"
        )
        self.assertEqual(resp_create.status_code, status.HTTP_202_ACCEPTED)

        # Check create Item's name is expected one that is generated from autoname pattern
        self.assertEqual(
            Entry.objects.filter(schema=model_sg).last().name,
            "[LB0001] test.example.com:8080 #123.456",
        )

    @patch("entry.tasks.edit_entry_v2.delay", Mock(side_effect=tasks.edit_entry_v2))
    def test_update_for_autoname_item(self):
        (model_lb, model_sg) = self._create_lb_models_for_autoname()

        item_lb = self.add_entry(self.user, "LB0001", model_lb)
        item_sg = self.add_entry(self.user, "ChangingName", model_sg)

        # attr = item_sg.schema.attrs.get(name="label")
        params = {
            "name": "ChangingName",
            "attrs": [
                {"id": model_sg.attrs.get(name="LB").id, "value": item_lb.id},
                {"id": model_sg.attrs.get(name="label").id, "value": "This is test ServiceGroup"},
                {"id": model_sg.attrs.get(name="domain").id, "value": "test.example.com"},
                {"id": model_sg.attrs.get(name="port").id, "value": "8080"},
                {"id": model_sg.attrs.get(name="number").id, "value": 123.456},
                {
                    "id": model_sg.attrs.get(name="dict").id,
                    "value": {"id": item_lb.id, "name": "hoge"},
                },
            ],
        }
        resp = self.client.put(
            "/entry/api/v2/%s/" % item_sg.id, json.dumps(params), "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        # Check updated Item's name is expected one that is generated from autoname pattern
        item_sg.refresh_from_db()
        self.assertEqual(item_sg.name, "[LB0001] test.example.com:8080 #123.456")

    @patch("entry.tasks.import_entries_v2.delay", Mock(side_effect=tasks.import_entries_v2))
    def test_import_update_items_for_autoname(self):
        (model_lb, model_sg) = self._create_lb_models_for_autoname()

        item_lbs = [self.add_entry(self.user, "LB%04d" % x, model_lb) for x in range(3)]

        importing_params = [
            {
                "entity": model_sg.name,
                "entries": [
                    {
                        "name": "ShouldBeChanged",
                        "attrs": [
                            {"name": "LB", "value": item_lbs[index].name},
                            {"name": "port", "value": port},
                            {"name": "domain", "value": domain},
                        ],
                    }
                    for index, (domain, port) in enumerate(
                        [
                            ("hoge.example.com", "8080"),
                            ("fuga.example.com", "9090"),
                            ("puyo.example.com", "10000"),
                        ]
                    )
                ],
            }
        ]
        resp = self.client.post(
            "/entry/api/v2/import/", yaml.dump(importing_params), "application/yaml"
        )
        self.assertEqual(resp.status_code, 200)

        # check Item name is determined by its attribute values
        self.assertEqual(
            [
                "[LB0000] hoge.example.com:8080",
                "[LB0001] fuga.example.com:9090",
                "[LB0002] puyo.example.com:10000",
            ],
            [x.name for x in Entry.objects.filter(schema=model_sg).order_by("id")],
        )

    @patch("entry.tasks.create_entry_v2.delay", Mock(side_effect=tasks.create_entry_v2))
    def test_array_number_with_null_values(self):
        """Test array number with null/None values"""
        entry_name = "test_entry_array_number_with_nulls"
        number_values = [123.45, None, 67.89, None, 0.0]

        nums_entity_attr = self.entity.attrs.get(name="nums")

        payload = {
            "name": entry_name,
            "schema": self.entity.id,
            "attrs": [{"id": nums_entity_attr.id, "value": number_values}],
        }

        resp_create = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload, "application/json"
        )
        self.assertEqual(resp_create.status_code, status.HTTP_202_ACCEPTED, resp_create.content)

        created_entry = Entry.objects.filter(name=entry_name, schema=self.entity).first()
        self.assertIsNotNone(created_entry, "Entry was not created")

        resp_get = self.client.get(f"/entry/api/v2/{created_entry.id}/")
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK, resp_get.content)
        retrieved_data = resp_get.json()

        nums_attr_retrieved = None
        for attr in retrieved_data.get("attrs", []):
            if attr["schema"]["name"] == "nums":
                nums_attr_retrieved = attr
                break
        self.assertIsNotNone(nums_attr_retrieved)

        retrieved_values = nums_attr_retrieved["value"]["as_array_number"]
        expected_values = [123.45, None, 67.89, None, 0.0]
        self.assertEqual(len(retrieved_values), len(expected_values))

        for i, expected_val in enumerate(expected_values):
            if expected_val is None:
                self.assertIsNone(retrieved_values[i])
            else:
                self.assertAlmostEqual(retrieved_values[i], expected_val, places=5)

    @patch("entry.tasks.create_entry_v2.delay", Mock(side_effect=tasks.create_entry_v2))
    def test_array_number_empty_array(self):
        """Test array number with empty array"""
        entry_name = "test_entry_array_number_empty"
        number_values = []

        nums_entity_attr = self.entity.attrs.get(name="nums")

        payload = {
            "name": entry_name,
            "schema": self.entity.id,
            "attrs": [{"id": nums_entity_attr.id, "value": number_values}],
        }

        resp_create = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload, "application/json"
        )
        self.assertEqual(resp_create.status_code, status.HTTP_202_ACCEPTED, resp_create.content)

        created_entry = Entry.objects.filter(name=entry_name, schema=self.entity).first()
        self.assertIsNotNone(created_entry, "Entry was not created")

        resp_get = self.client.get(f"/entry/api/v2/{created_entry.id}/")
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK, resp_get.content)
        retrieved_data = resp_get.json()

        nums_attr_retrieved = None
        for attr in retrieved_data.get("attrs", []):
            if attr["schema"]["name"] == "nums":
                nums_attr_retrieved = attr
                break
        self.assertIsNotNone(nums_attr_retrieved)

        retrieved_values = nums_attr_retrieved["value"]["as_array_number"]
        self.assertEqual(retrieved_values, [])

    @patch("entry.tasks.create_entry_v2.delay", Mock(side_effect=tasks.create_entry_v2))
    def test_array_number_edge_case_values(self):
        """Test array number with edge case values like large numbers, small numbers, etc."""
        entry_name = "test_entry_array_number_edge_cases"
        # Test with various edge case numbers
        number_values = [
            0,
            -0,
            1e10,  # Large positive number
            -1e10,  # Large negative number
            1e-10,  # Very small positive number
            -1e-10,  # Very small negative number
            math.pi,  # Irrational number
            math.e,  # Euler's number
        ]

        nums_entity_attr = self.entity.attrs.get(name="nums")

        payload = {
            "name": entry_name,
            "schema": self.entity.id,
            "attrs": [{"id": nums_entity_attr.id, "value": number_values}],
        }

        resp_create = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload, "application/json"
        )
        self.assertEqual(resp_create.status_code, status.HTTP_202_ACCEPTED, resp_create.content)

        created_entry = Entry.objects.filter(name=entry_name, schema=self.entity).first()
        self.assertIsNotNone(created_entry, "Entry was not created")

        resp_get = self.client.get(f"/entry/api/v2/{created_entry.id}/")
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK, resp_get.content)
        retrieved_data = resp_get.json()

        nums_attr_retrieved = None
        for attr in retrieved_data.get("attrs", []):
            if attr["schema"]["name"] == "nums":
                nums_attr_retrieved = attr
                break
        self.assertIsNotNone(nums_attr_retrieved)

        retrieved_values = nums_attr_retrieved["value"]["as_array_number"]
        self.assertEqual(len(retrieved_values), len(number_values))

        for i, expected_val in enumerate(number_values):
            self.assertAlmostEqual(retrieved_values[i], expected_val, places=10)

    def test_array_number_invalid_values(self):
        """Test array number with invalid string values"""
        entry_name = "test_entry_array_number_invalid"
        # Mix of valid numbers and invalid strings
        invalid_values = [123.45, "not-a-number", 67.89, "invalid", ""]

        nums_entity_attr = self.entity.attrs.get(name="nums")

        payload = {
            "name": entry_name,
            "schema": self.entity.id,
            "attrs": [{"id": nums_entity_attr.id, "value": invalid_values}],
        }

        resp_create = self.client.post(
            f"/entity/api/v2/{self.entity.id}/entries/", payload, "application/json"
        )
        # This should return a validation error
        self.assertEqual(
            resp_create.status_code,
            status.HTTP_400_BAD_REQUEST,
            resp_create.content,
        )

    @patch("entry.tasks.bulk_update_entries.delay", Mock(side_effect=tasks.bulk_update_entries))
    def test_bulk_update_items(self):
        # Create items for bulk updating
        for index, str_val in enumerate(["foo", "bar", "baz"]):
            self.add_entry(
                self.user,
                "item-%s" % index,
                self.entity,
                values={
                    "val": str_val,
                },
            )

        # Make parameters for sending server
        updating_attr = self.entity.attrs.get(name="val")

        params = {
            "value": {"id": updating_attr.id, "value": "updated"},
            "modelid": self.entity.id,
            "attrinfo": [{"name": "val", "filter_key": FilterKey.TEXT_CONTAINED, "keyword": "ba"}],
            "hint_entry": {"filter_key": EntryFilterKey.TEXT_CONTAINED, "keyword": "item"},
        }
        resp = self.client.put(
            "/entry/api/v2/bulk/",
            params,
            "application/json",
        )
        self.assertEqual(resp.status_code, 202)

        # Check items are pudate expectedly
        expected_values = [
            ("item-0", "foo"),
            ("item-1", "updated"),  # this one should be updated from bar to updated
            ("item-2", "updated"),  # this one should be updated from baz to updated
        ]

        for itemname, expected_value in expected_values:
            item = Entry.objects.get(name=itemname, schema=self.entity)
            self.assertEqual(item.get_attrv("val").value, expected_value)

    @patch("entry.tasks.bulk_update_entries.delay", Mock(side_effect=tasks.bulk_update_entries))
    def test_bulk_update_items_with_referral_name_filter(self):
        """
        This tests bulk update when referral_name filter is used for advanced search.
        """
        # Create items that are referred by other items
        target_items = [self.add_entry(self.user, f"item-{i}", self.entity) for i in range(3)]
        [
            self.add_entry(
                self.user, "refering-item-%s" % v, self.entity, values={"ref": target_items[i]}
            )
            for (i, v) in enumerate(["foo", "bar", "baz"])
        ]

        # Make parameters for sending server
        updating_attr = self.entity.attrs.get(name="val")
        params = {
            "value": {"id": updating_attr.id, "value": "updated"},
            "modelid": self.entity.id,
            "referral_name": "ba",  # this would be matched with "bar" and "baz"
        }
        resp = self.client.put(
            "/entry/api/v2/bulk/",
            params,
            "application/json",
        )
        self.assertEqual(resp.status_code, 202)

        # Check items are pudate expectedly
        expected_values = [
            ("item-0", ""),
            ("item-1", "updated"),  # this one should be updated from bar to updated
            ("item-2", "updated"),  # this one should be updated from baz to updated
        ]

        for itemname, expected_value in expected_values:
            item = Entry.objects.get(name=itemname, schema=self.entity)
            self.assertEqual(item.get_attrv("val").value, expected_value)

    @patch.object(Job, "is_canceled", Mock(return_value=True))
    @patch("entry.tasks.bulk_update_entries.delay", Mock(side_effect=tasks.bulk_update_entries))
    def test_bulk_update_items_with_canceled(self):
        """
        This tests bulk update when the job is canceled during processing.
        """
        # Create items for bulk updating
        for index, str_val in enumerate(["foo", "bar", "baz"]):
            self.add_entry(
                self.user,
                "item-%s" % index,
                self.entity,
                values={
                    "val": str_val,
                },
            )

        # Make parameters for sending server
        updating_attr = self.entity.attrs.get(name="val")

        params = {
            "value": {"id": updating_attr.id, "value": "updated"},
            "modelid": self.entity.id,
            "attrinfo": [],
        }
        resp = self.client.put(
            "/entry/api/v2/bulk/",
            params,
            "application/json",
        )
        self.assertEqual(resp.status_code, 202)

        # Check items are not updated due to cancellation
        expected_values = [
            # These won't be updated because the job is canceled
            ("item-0", "foo"),
            ("item-1", "bar"),
            ("item-2", "baz"),
        ]
        for itemname, expected_value in expected_values:
            item = Entry.objects.get(name=itemname, schema=self.entity)
            self.assertEqual(item.get_attrv("val").value, expected_value)

        # check job text shows expected message
        job = Job.objects.filter(operation=JobOperation.BULK_EDIT_ENTRY).last()
        self.assertEqual(job.text, "Now updating... (progress: [    1/    3])")
