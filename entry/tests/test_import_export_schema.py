"""Contract tests for the entry import/export pydantic schemas.

These pin the export path and the import path to the same data contract:
everything the exporter is able to emit must be describable by the typed import
params, malformed params must be rejected, and the DRF boundary serializers must
keep mirroring the pydantic contract they feed.
"""

from django.test import SimpleTestCase
from pydantic import ValidationError

from entry.api_v2.serializers import (
    AttributeData,
    AttributeDataSerializer,
    EntryImportAttributeSerializer,
    EntryImportEntitySerializer,
    EntryImportEntriesSerializer,
    ExportedEntityEntries,
    ExportedEntry,
    ExportedEntryAttribute,
)
from job.params import ImportedAttribute, ImportedEntry, ImportEntryParams


class ImportExportSchemaStructureTest(SimpleTestCase):
    """The import contract must be able to describe every exported field."""

    def test_attribute_fields_cover_export(self):
        self.assertTrue(
            set(ExportedEntryAttribute.model_fields) <= set(ImportedAttribute.model_fields)
        )

    def test_entry_fields_cover_export(self):
        # ``referrals`` is export-only metadata and is intentionally not imported.
        self.assertTrue(
            set(ExportedEntry.model_fields) - {"referrals"} <= set(ImportedEntry.model_fields)
        )

    def test_entity_entries_fields_cover_export(self):
        self.assertTrue(
            set(ExportedEntityEntries.model_fields) <= set(ImportEntryParams.model_fields)
        )

    def test_drf_boundary_matches_pydantic_contract(self):
        """The OpenAPI boundary and the import contract must not drift apart.

        The DRF serializers generate the request body and the request-level
        errors; the typed job params (pydantic) are what the tasks read.  If
        someone adds a field to one side only, this fails.
        """
        self.assertEqual(
            set(EntryImportEntitySerializer().fields) | {"preview_job_id"},
            set(ImportEntryParams.model_fields),
        )
        self.assertEqual(
            set(EntryImportEntriesSerializer().fields), set(ImportedEntry.model_fields)
        )
        self.assertEqual(
            set(EntryImportAttributeSerializer().fields), set(ImportedAttribute.model_fields)
        )


class ImportParamsValidationTest(SimpleTestCase):
    def test_accepts_the_import_shape(self):
        params = ImportEntryParams.model_validate(
            {
                "entity": "test-entity",
                "entries": [
                    {
                        "id": 1,
                        "name": "test-entry",
                        "attrs": [{"name": "text", "value": "foo"}],
                    }
                ],
            }
        )

        self.assertEqual(params.entity, "test-entity")
        self.assertEqual(len(params.entries), 1)
        self.assertEqual(params.entries[0].name, "test-entry")
        self.assertEqual(params.entries[0].attrs[0].name, "text")
        self.assertIsNone(params.preview_job_id)

    def test_attrs_default_to_empty_list(self):
        params = ImportEntryParams.model_validate(
            {"entity": "test-entity", "entries": [{"name": "test-entry"}]}
        )
        self.assertEqual(params.entries[0].attrs, [])

    def test_value_defaults_to_none(self):
        params = ImportEntryParams.model_validate(
            {"entity": "test-entity", "entries": [{"name": "e", "attrs": [{"name": "val"}]}]}
        )
        self.assertIsNone(params.entries[0].attrs[0].value)

    def test_rejects_missing_entity(self):
        with self.assertRaises(ValidationError):
            ImportEntryParams.model_validate({"entries": []})

    def test_rejects_missing_entry_name(self):
        with self.assertRaises(ValidationError):
            ImportEntryParams.model_validate({"entity": "test-entity", "entries": [{"attrs": []}]})

    def test_rejects_wrong_root_type(self):
        with self.assertRaises(ValidationError):
            ImportEntryParams.model_validate([{"entity": "test-entity", "entries": []}])

    def test_rejects_unknown_fields(self):
        # Job params are a fail-closed contract; export-only blocks such as
        # ``referrals`` are dropped at the DRF boundary, never smuggled in here.
        with self.assertRaises(ValidationError):
            ImportEntryParams.model_validate(
                {"entity": "test-entity", "entries": [], "referrals": []}
            )


class AttributeDataContractTest(SimpleTestCase):
    def test_drf_boundary_matches_pydantic_contract(self):
        # AttributeData is the pydantic validation contract for attribute data
        # and AttributeDataSerializer is only the API boundary that feeds it.
        self.assertEqual(set(AttributeDataSerializer().fields), set(AttributeData.model_fields))
