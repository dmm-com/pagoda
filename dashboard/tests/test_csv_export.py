import csv
import io
from unittest.mock import Mock

from django.test import SimpleTestCase

from airone.lib.elasticsearch import AdvancedSearchResultRecord
from airone.lib.types import AttrType
from dashboard.tasks import _csv_export
from entry.tasks import _csv_export_v2


class CsvExportTest(SimpleTestCase):
    def test_every_array_element_gets_a_row_with_repeated_item_name(self):
        cases = [
            (
                AttrType.ARRAY_STRING,
                ['first,"value"', "second\nline"],
                ['first,"value"', "second\nline"],
            ),
            (AttrType.ARRAY_NUMBER, [2, 0, -1], ["2", "0", "-1"]),
            (
                AttrType.ARRAY_OBJECT,
                [{"id": 1, "name": "ip1"}, {"id": 2, "name": "ip2"}],
                ["ip1", "ip2"],
            ),
            (AttrType.ARRAY_GROUP, [{"name": "group1"}, {"name": "group2"}], ["group1", "group2"]),
            (AttrType.ARRAY_ROLE, [{"name": "role1"}, {"name": "role2"}], ["role1", "role2"]),
            (
                AttrType.ARRAY_NAMED_OBJECT,
                [{"nic1": {"name": "ip1"}}, {"nic2": None}],
                ["nic1: ip1", "nic2: "],
            ),
            (
                AttrType.ARRAY_NAMED_OBJECT_BOOLEAN,
                [{"nic1": {"name": "ip1", "boolean": False}}, {"nic2": {"name": "ip2"}}],
                ["nic1: ip1", "nic2: ip2"],
            ),
            (
                AttrType.MULTI_SELECT,
                [{"value": "a", "label": "A"}, {"value": "b", "label": "B"}],
                ["A", "B"],
            ),
            (AttrType.ARRAY_STRING, [], [""]),
        ]
        for exporter in [_csv_export, _csv_export_v2]:
            for attr_type, values, expected in cases:
                with self.subTest(exporter=exporter.__name__, attr_type=attr_type, values=values):
                    record = AdvancedSearchResultRecord(
                        entity={"id": 1, "name": "VM"},
                        entry={"id": 2, "name": "vm7264"},
                        attrs={
                            "array": {"type": attr_type, "value": values},
                            "scalar": {"type": AttrType.STRING, "value": "same"},
                        },
                        is_readable=True,
                    )
                    original = record.model_dump()
                    output = exporter(
                        Mock(is_canceled=Mock(return_value=False)),
                        [record],
                        {"attrinfo": [{"name": "array"}, {"name": "scalar"}]},
                        False,
                    )
                    prefix = ["vm7264", "VM"] if exporter is _csv_export else ["vm7264"]
                    self.assertEqual(
                        list(csv.reader(io.StringIO(output.getvalue())))[1:],
                        [prefix + [item, "same"] for item in expected],
                    )
                    self.assertEqual(record.model_dump(), original)

    def test_multiple_arrays_repeat_other_values_for_all_combinations(self):
        record = AdvancedSearchResultRecord(
            entity={"id": 1, "name": "VM"},
            entry={"id": 2, "name": "vm7264"},
            attrs={
                "ips": {"type": AttrType.ARRAY_STRING, "value": ["ip1", "ip2"]},
                "tags": {"type": AttrType.ARRAY_STRING, "value": ["tag1", "tag2", "tag3"]},
                "scalar": {"type": AttrType.STRING, "value": "same"},
            },
            is_readable=True,
        )
        for exporter in [_csv_export, _csv_export_v2]:
            with self.subTest(exporter=exporter.__name__):
                output = exporter(
                    Mock(is_canceled=Mock(return_value=False)),
                    [record],
                    {"attrinfo": [{"name": name} for name in ["ips", "tags", "scalar"]]},
                    False,
                )
                prefix = ["vm7264", "VM"] if exporter is _csv_export else ["vm7264"]
                self.assertEqual(
                    list(csv.reader(io.StringIO(output.getvalue())))[1:],
                    [
                        prefix + [ip, tag, "same"]
                        for ip in ["ip1", "ip2"]
                        for tag in ["tag1", "tag2", "tag3"]
                    ],
                )
