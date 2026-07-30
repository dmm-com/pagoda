import traceback
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from airone.lib.nplusone import QueryDetector, normalize_sql


class NormalizeSQLTest(SimpleTestCase):
    def test_normalizes_values_but_preserves_query_shape(self):
        first = "SELECT * FROM user WHERE id = 1 AND name = 'alice'"
        second = "SELECT * FROM user WHERE id = 42 AND name = 'bob'"

        self.assertEqual(normalize_sql(first), normalize_sql(second))


class QueryDetectorTest(SimpleTestCase):
    def test_reports_repeated_select_with_actionable_location(self):
        detector = QueryDetector(min_repeats=3)
        stack = [traceback.FrameSummary("/tmp/outside.py", 1, "outside")]
        for user_id in range(3):
            detector.observe(f"SELECT username FROM user WHERE id = {user_id}", stack=stack)

        findings = detector.findings()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].occurrences, 3)
        self.assertIn("load related rows in bulk", findings[0].hint)

    def test_prefers_application_source_over_virtual_environment(self):
        detector = QueryDetector(min_repeats=2)
        root = Path(settings.BASE_DIR)
        stack = [
            traceback.FrameSummary(str(root / "group/api_v2/serializers.py"), 31, "get_members"),
            traceback.FrameSummary(str(root / ".venv/django/db/utils.py"), 92, "execute"),
        ]
        detector.observe("SELECT * FROM user WHERE group_id = 1", stack=stack)
        detector.observe("SELECT * FROM user WHERE group_id = 2", stack=stack)

        finding = detector.findings()[0]

        self.assertEqual(finding.location.path, "group/api_v2/serializers.py")
        self.assertIn("prefetch_related", finding.hint)

    def test_ignores_repeated_writes(self):
        detector = QueryDetector(min_repeats=2)
        detector.observe("INSERT INTO user (username) VALUES ('alice')", stack=[])
        detector.observe("INSERT INTO user (username) VALUES ('bob')", stack=[])

        self.assertEqual(detector.findings(), [])

    def test_rejects_threshold_below_two(self):
        with self.assertRaisesRegex(ValueError, "at least 2"):
            QueryDetector(min_repeats=1)
