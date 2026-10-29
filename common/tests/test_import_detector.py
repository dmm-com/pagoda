from django.test import SimpleTestCase

from common.lib.import_detector import ImportType, UnknownImportFormatError, detect_import_type


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
