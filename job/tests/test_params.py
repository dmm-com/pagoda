import json
from datetime import date

from django.test import SimpleTestCase
from pydantic import BaseModel, ConfigDict, RootModel, ValidationError

from job.models import JobOperation
from job.params import (
    CORE_JOB_PARAMS,
    EmptyParams,
    assert_core_registry_complete,
    get_job_params_contract,
    parse_job_params,
    register_job_params,
    serialize_job_params,
    unregister_job_params,
    validate_job_params,
)


class JobParamsTest(SimpleTestCase):
    VALID_CORE_PARAMS = {
        1: {"entry_name": "a", "attrs": [{"id": "1", "value": []}]},
        2: {
            "entry_name": "a",
            "attrs": [{"entity_attr_id": "1", "id": "", "value": []}],
        },
        3: {},
        4: {"new_name_list": ["copy"], "post_data": {}},
        5: [{"name": "a", "attrs": {}}],
        6: {"export_format": "yaml", "target_id": 1},
        7: {},
        8: {"entities": [1], "attrinfo": [], "export_style": "yaml"},
        9: {},
        10: {"name": "E", "note": "", "is_toplevel": False, "attrs": []},
        11: {"name": "E", "note": "", "is_toplevel": False, "attrs": []},
        12: {},
        13: {},
        14: {},
        15: {},
        16: {"new_name_list": ["copy"], "new_name": "copy", "post_data": {}},
        17: {"entity": "E", "entries": []},
        18: {"group_id": 1},
        19: {"role_id": 1},
        20: {"export_format": "csv", "target_id": 1},
        21: {"is_update": True},
        22: {"entities": [1], "attrinfo": [], "export_style": "csv"},
        23: [],
        24: {"name": "E"},
        25: {},
        26: {},
        27: {"schema": 1, "name": "a"},
        28: {},
        29: {},
        30: [],
        31: {"modelid": 1, "value": {"id": 1, "value": None}},
        32: {"Entity": [], "EntityAttr": []},
        33: {"entity": "E", "entries": []},
    }

    def test_all_core_operations_have_contracts(self) -> None:
        assert_core_registry_complete()
        self.assertEqual(set(CORE_JOB_PARAMS), {int(operation) for operation in JobOperation})

    def test_every_core_contract_accepts_its_producer_shape(self) -> None:
        self.assertEqual(set(self.VALID_CORE_PARAMS), set(CORE_JOB_PARAMS))
        for operation, payload in self.VALID_CORE_PARAMS.items():
            with self.subTest(operation=operation):
                validate_job_params(operation, payload)

    def test_every_core_contract_rejects_wrong_root(self) -> None:
        list_root_operations = {
            int(JobOperation.IMPORT_ENTRY),
            int(JobOperation.MAY_INVOKE_TRIGGER),
            int(JobOperation.IMPORT_ROLE_V2),
        }
        for operation in CORE_JOB_PARAMS:
            wrong_root = {} if operation in list_root_operations else []
            with self.subTest(operation=operation), self.assertRaises(ValidationError):
                validate_job_params(operation, wrong_root)

    def test_every_object_root_contract_rejects_unknown_top_level_field(self) -> None:
        list_root_operations = {
            int(JobOperation.IMPORT_ENTRY),
            int(JobOperation.MAY_INVOKE_TRIGGER),
            int(JobOperation.IMPORT_ROLE_V2),
        }
        for operation, payload in self.VALID_CORE_PARAMS.items():
            if operation in list_root_operations:
                continue
            mutated = {**payload, "unknown_job_parameter": True}
            with self.subTest(operation=operation), self.assertRaises(ValidationError):
                validate_job_params(operation, mutated)

    def test_required_top_level_fields_cannot_be_removed(self) -> None:
        for operation, contract in CORE_JOB_PARAMS.items():
            payload = self.VALID_CORE_PARAMS[operation]
            if not isinstance(payload, dict):
                continue
            required_fields = [
                field.alias or name
                for name, field in contract.model_fields.items()
                if field.is_required()
            ]
            for field_name in required_fields:
                if field_name not in payload:
                    continue
                mutated = {key: value for key, value in payload.items() if key != field_name}
                with (
                    self.subTest(operation=operation, field=field_name),
                    self.assertRaises(ValidationError),
                ):
                    validate_job_params(operation, mutated)

    def test_empty_params_reject_extra_fields(self) -> None:
        with self.assertRaises(ValidationError):
            validate_job_params(JobOperation.DELETE_ENTRY, {"unexpected": True})

    def test_valid_object_root_and_canonical_json(self) -> None:
        payload = {"is_update": False}
        validated = validate_job_params(JobOperation.UPDATE_DOCUMENT, payload)
        self.assertFalse(validated.is_update)
        self.assertEqual(
            serialize_job_params(JobOperation.UPDATE_DOCUMENT, payload), '{"is_update":false}'
        )

    def test_invalid_object_root(self) -> None:
        with self.assertRaises(ValidationError):
            validate_job_params(JobOperation.UPDATE_DOCUMENT, {"is_update": "not-a-bool"})

    def test_bool_is_not_accepted_as_integer_id(self) -> None:
        with self.assertRaises(ValidationError):
            validate_job_params(JobOperation.GROUP_REGISTER_REFERRAL, {"group_id": True})
        with self.assertRaises(ValidationError):
            validate_job_params(
                JobOperation.EXPORT_ENTRY,
                {"export_format": "yaml", "target_id": False},
            )

    def test_list_root(self) -> None:
        payload = [{"name": "operators", "description": "Operations"}]
        validated = validate_job_params(JobOperation.IMPORT_ROLE_V2, payload)
        self.assertEqual(validated.root[0].name, "operators")
        self.assertEqual(
            serialize_job_params(JobOperation.IMPORT_ROLE_V2, payload),
            '[{"description":"Operations","name":"operators"}]',
        )

    def test_root_list_rejects_object(self) -> None:
        with self.assertRaises(ValidationError):
            validate_job_params(JobOperation.IMPORT_ROLE_V2, {"name": "operators"})

    def test_trigger_accepts_list_and_legacy_persisted_empty_object(self) -> None:
        list_value = validate_job_params(JobOperation.MAY_INVOKE_TRIGGER, [{"id": 1, "value": 2}])
        map_value = parse_job_params(JobOperation.MAY_INVOKE_TRIGGER, "{}")
        self.assertEqual(list_value.root[0].value, 2)
        self.assertEqual(map_value.root, [])
        with self.assertRaises(ValidationError):
            validate_job_params(JobOperation.MAY_INVOKE_TRIGGER, {})

    def test_legacy_entry_fixture_preserves_explicit_string_ids(self) -> None:
        payload = {
            "entry_name": "server-01",
            "attrs": [
                {
                    "entity_attr_id": "12",
                    "id": "",
                    "value": [{"data": "active", "index": "0"}],
                    "referral_key": [],
                }
            ],
        }
        validated = validate_job_params(JobOperation.EDIT_ENTRY, payload)
        self.assertEqual(validated.attrs[0].entity_attr_id, "12")
        self.assertEqual(validated.attrs[0].value[0].index, 0)
        with self.assertRaises(ValidationError):
            validate_job_params(
                JobOperation.EDIT_ENTRY,
                {**payload, "attrs": [{**payload["attrs"][0], "entity_attr_id": 12}]},
            )

    def test_copy_fixture_accepts_opaque_callback_post_data(self) -> None:
        payload = {
            "new_name_list": ["copy-1"],
            "post_data": {"copy_entry_names": ["copy-1"], "plugin_option": {"x": 1}},
        }
        validated = validate_job_params(JobOperation.COPY_ENTRY, payload)
        self.assertEqual(validated.post_data["plugin_option"], {"x": 1})

    def test_legacy_and_v2_import_fixtures_use_distinct_roots(self) -> None:
        legacy = [{"name": "server-01", "attrs": {"status": "active"}}]
        v2 = {
            "entity": "Server",
            "entries": [{"name": "server-01", "attrs": [{"name": "status", "value": "active"}]}],
        }
        self.assertEqual(
            validate_job_params(JobOperation.IMPORT_ENTRY, legacy).root[0].name, "server-01"
        )
        self.assertEqual(validate_job_params(JobOperation.IMPORT_ENTRY_V2, v2).entity, "Server")

    def test_import_params_preserve_approved_preview_linkage(self) -> None:
        """An import approved from a preview carries preview_job_id; keep it round-trippable."""

        payload = {"entity": "Server", "entries": [], "preview_job_id": 7}
        validated = validate_job_params(JobOperation.IMPORT_ENTRY_V2, payload)
        self.assertEqual(validated.preview_job_id, 7)
        # The preview job itself never sets the linkage, and it stays optional.
        self.assertIsNone(
            validate_job_params(JobOperation.IMPORT_ENTRY_V2, {"entity": "Server"}).preview_job_id
        )
        self.assertIsNone(
            validate_job_params(
                JobOperation.IMPORT_ENTRY_PREVIEW, {"entity": "Server"}
            ).preview_job_id
        )
        serialized = json.loads(serialize_job_params(JobOperation.IMPORT_ENTRY_V2, payload))
        self.assertEqual(serialized["preview_job_id"], 7)

    def test_preview_fixture_matches_import_serializer_root(self) -> None:
        payload = {
            "Entity": [{"id": 1, "name": "Server", "created_user": "admin"}],
            "EntityAttr": [
                {
                    "id": 2,
                    "name": "status",
                    "type": 1,
                    "entity": "Server",
                    "created_user": "admin",
                    "refer": "",
                }
            ],
        }
        validated = validate_job_params(JobOperation.IMPORT_ENTITY_PREVIEW, payload)
        self.assertEqual(validated.EntityAttr[0].entity, "Server")

    def test_role_import_fixture_matches_yaml_contract(self) -> None:
        payload = [
            {
                "name": "operators",
                "users": ["alice"],
                "groups": ["operations"],
                "admin_users": ["admin"],
                "admin_groups": [],
                "permissions": [{"obj_id": 1, "permission": "full"}],
            }
        ]
        validated = validate_job_params(JobOperation.IMPORT_ROLE_V2, payload)
        self.assertEqual(validated.root[0].users, ["alice"])

    def test_trigger_fixtures_accept_v1_and_v2_attribute_shapes(self) -> None:
        v1 = [{"entity_attr_id": "12", "id": "", "value": [], "referral_key": []}]
        v2 = [{"id": 12, "value": {"id": 34, "name": "target"}}]
        self.assertEqual(validate_job_params(JobOperation.MAY_INVOKE_TRIGGER, v1).root[0].id, "")
        self.assertEqual(validate_job_params(JobOperation.MAY_INVOKE_TRIGGER, v2).root[0].id, 12)

    def test_parse_persisted_json(self) -> None:
        parsed = parse_job_params(JobOperation.COPY_ENTRY, '{"new_name_list":["copy"]}')
        self.assertEqual(parsed.new_name_list, ["copy"])

    def test_parse_rejects_malformed_json(self) -> None:
        with self.assertRaises(ValidationError):
            parse_job_params(JobOperation.COPY_ENTRY, '{"new_name_list":')

    def test_json_mode_serializes_dates(self) -> None:
        class JsonModeProbe(BaseModel):
            value: date

        operation = 10_001
        register_job_params(operation, JsonModeProbe)
        self.addCleanup(unregister_job_params, operation)
        self.assertEqual(
            serialize_job_params(operation, {"value": date(2026, 8, 29)}),
            '{"value":"2026-08-29"}',
        )

    def test_serialization_preserves_explicit_none(self) -> None:
        class NullableParams(BaseModel):
            value: str | None = "default"

        operation = 10_004
        register_job_params(operation, NullableParams)
        self.addCleanup(unregister_job_params, operation)
        serialized = serialize_job_params(operation, {"value": None})
        self.assertEqual(serialized, '{"value":null}')
        self.assertIsNone(parse_job_params(operation, serialized).value)

    def test_validated_models_and_root_models_are_frozen(self) -> None:
        object_value = validate_job_params(JobOperation.UPDATE_DOCUMENT, {"is_update": True})
        root_value = validate_job_params(JobOperation.IMPORT_ROLE_V2, [])
        with self.assertRaises(ValidationError):
            object_value.is_update = False
        with self.assertRaises(ValidationError):
            root_value.root = []

    def test_custom_contract_registration(self) -> None:
        class CustomParams(BaseModel):
            model_config = ConfigDict(extra="forbid")
            names: list[str]

        operation = 10_002
        register_job_params(operation, CustomParams)
        self.addCleanup(unregister_job_params, operation)
        self.assertIs(get_job_params_contract(operation), CustomParams)
        self.assertEqual(validate_job_params(operation, {"names": ["a"]}).names, ["a"])
        with self.assertRaises(ValueError):
            register_job_params(operation, CustomParams)

    def test_custom_root_contract(self) -> None:
        class CustomRoot(RootModel[list[int]]):
            pass

        operation = 10_003
        register_job_params(operation, CustomRoot)
        self.addCleanup(unregister_job_params, operation)
        self.assertEqual(parse_job_params(operation, "[1,2]").root, [1, 2])

    def test_core_contract_cannot_be_replaced(self) -> None:
        with self.assertRaises(ValueError):
            register_job_params(JobOperation.DELETE_ENTRY, EmptyParams)

    def test_unknown_operation_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            validate_job_params(999_999, {})
