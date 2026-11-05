from django.test import SimpleTestCase

from common.lib.import_detector import (
    ImportType,
    UnknownImportFormatError,
    detect_import_type,
    parse_import_document,
    unwrap_envelope,
    wrap_envelope,
)


class ImportDetectorTest(SimpleTestCase):
    def test_detect(self) -> None:
        cases = [
            ({"Entity": [], "EntityAttr": []}, ImportType.ENTITY),
            ([{"entity": "E", "entries": []}], ImportType.ENTRY),
            ([{"username": "u", "email": "e", "groups": "A,B"}], ImportType.USER),
            ([{"name": "u", "groups": "A"}], ImportType.USER),
            ([{"name": "r", "users": [], "groups": [], "admin_users": []}], ImportType.ROLE),
            ([{"name": "r", "groups": ["g"]}], ImportType.ROLE),
            ([{"name": "g"}, {"id": 1, "name": "h"}], ImportType.GROUP),
        ]
        for data, expected in cases:
            with self.subTest(data=data):
                self.assertEqual(detect_import_type(data), expected)

    def test_reject(self) -> None:
        cases = [
            [],
            {},
            {"foo": 1},
            "text",
            None,
            [{}],
            [{"unknown": 1}],
            ["not a dict"],
            [{"name": "g"}, {"username": "u", "email": "e", "groups": ""}],
            [{"entity": "E", "entries": []}, {"name": "g"}],
        ]
        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(UnknownImportFormatError):
                    detect_import_type(data)


class ImportEnvelopeTest(SimpleTestCase):
    def test_envelope_declares_type(self) -> None:
        cases = [
            (ImportType.ENTITY, {"Entity": [], "EntityAttr": []}),
            (ImportType.ENTRY, [{"entity": "E", "entries": []}]),
            (ImportType.USER, [{"username": "u", "email": "e", "groups": "A,B"}]),
            (ImportType.GROUP, [{"id": 1, "name": "g"}]),
            (ImportType.ROLE, [{"name": "r", "users": [], "groups": ["g"]}]),
        ]
        for import_type, payload in cases:
            with self.subTest(import_type=import_type):
                document = parse_import_document(wrap_envelope(import_type, payload))
                self.assertEqual(document.import_type, import_type)
                self.assertEqual(document.payload, payload)
                self.assertEqual(
                    detect_import_type(wrap_envelope(import_type, payload)), import_type
                )

    def test_envelope_ignores_extra_keys(self) -> None:
        data = {"import_type": "group", "version": 2, "data": [{"id": 1, "name": "g"}]}
        document = parse_import_document(data)
        self.assertEqual(document.import_type, ImportType.GROUP)
        self.assertEqual(document.payload, [{"id": 1, "name": "g"}])

    def test_legacy_document_is_passed_through(self) -> None:
        data = [{"name": "g"}]
        self.assertEqual(parse_import_document(data), (ImportType.GROUP, data))
        self.assertEqual(unwrap_envelope(data), (None, data))

    def test_envelope_declared_type_wins_without_scanning_payload(self) -> None:
        # The payload is not inspected, so neither an unknown shape nor a shape that
        # looks like another type changes the declared type; the serializers reject bad payloads.
        unknown = wrap_envelope(ImportType.USER, [{"future_field": 1}])
        self.assertEqual(detect_import_type(unknown), ImportType.USER)

        mislabelled = wrap_envelope(ImportType.USER, [{"id": 1, "name": "g"}])
        self.assertEqual(parse_import_document(mislabelled).import_type, ImportType.USER)
        self.assertEqual(parse_import_document(mislabelled).payload, [{"id": 1, "name": "g"}])

    def test_envelope_rejects_bad_envelope(self) -> None:
        cases = [
            {"import_type": "unknown", "data": [{"name": "g"}]},
            {"import_type": ["group"], "data": [{"name": "g"}]},
            {"import_type": "group"},
        ]
        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(UnknownImportFormatError):
                    detect_import_type(data)
