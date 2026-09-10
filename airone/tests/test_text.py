import unittest

from airone.lib.text import normalize_search_text


class NormalizeSearchTextTest(unittest.TestCase):
    def test_normalizes_width_and_case(self) -> None:
        self.assertEqual(
            normalize_search_text("ﾊﾝｶｸ-ＢＩＧ-LARGE"),
            "ハンカク-big-large",
        )

    def test_normalizes_japanese_search_text(self) -> None:
        value = normalize_search_text("ﾊﾝｶｸ-ＢＩＧ-LARGE")
        self.assertIn(normalize_search_text("ハンカク-big"), value)
