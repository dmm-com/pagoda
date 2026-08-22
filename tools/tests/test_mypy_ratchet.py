import subprocess
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from tools.mypy_ratchet import (
    Diagnostic,
    RatchetError,
    new_diagnostics,
    parse_mypy_output,
    run_mypy,
)


class MypyRatchetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("/temporary/source")

    def test_parser_normalizes_positions_and_counts_duplicate_errors(self) -> None:
        output = "\n".join(
            [
                '{"file":"entry/views.py","line":10,"column":3,'
                '"message":"Problem","code":"arg-type","severity":"error"}',
                '{"file":"entry/views.py","line":99,"column":7,'
                '"message":"Problem","code":"arg-type","severity":"error"}',
                '{"file":"entry/views.py","line":99,"column":7,'
                '"message":"Extra context","code":null,"severity":"note"}',
            ]
        )

        self.assertEqual(
            parse_mypy_output(output, root=self.root),
            Counter({Diagnostic("entry/views.py", "Problem", "arg-type"): 2}),
        )

    def test_parser_normalizes_absolute_path(self) -> None:
        output = (
            f'{{"file":"{self.root}/entry/views.py","line":1,"column":null,'
            '"message":"Problem","code":"misc","severity":"error"}'
        )

        self.assertEqual(
            parse_mypy_output(output, root=self.root),
            Counter({Diagnostic("entry/views.py", "Problem", "misc"): 1}),
        )

    def test_parser_fails_closed_on_unknown_output(self) -> None:
        with self.assertRaisesRegex(RatchetError, "could not parse"):
            parse_mypy_output("unexpected output", root=self.root)

    def test_multiset_comparison_reports_only_added_occurrences(self) -> None:
        first = Diagnostic("entry/views.py", "Problem", "arg-type")
        second = Diagnostic("entry/views.py", "Other", "return-value")
        base = Counter({first: 2})
        current = Counter({first: 3, second: 1})

        self.assertEqual(new_diagnostics(base, current), Counter({first: 1, second: 1}))

    def test_multiset_comparison_tolerates_file_renames(self) -> None:
        old = Diagnostic("entry/old.py", "Problem", "arg-type")
        renamed = Diagnostic("entry/new.py", "Problem", "arg-type")

        self.assertEqual(
            new_diagnostics(
                Counter({old: 1}),
                Counter({renamed: 1}),
                {"entry/new.py": "entry/old.py"},
            ),
            Counter(),
        )

    def test_run_mypy_fails_closed_on_non_diagnostic_exit(self) -> None:
        for returncode in (2, 3, 127):
            with self.subTest(returncode=returncode):
                result = subprocess.CompletedProcess(
                    ["mypy"], returncode, "", "configuration failed"
                )
                with patch("tools.mypy_ratchet._run", return_value=result):
                    with self.assertRaisesRegex(RatchetError, f"exit code {returncode}"):
                        run_mypy(self.root)

    def test_run_mypy_fails_when_exit_one_has_no_errors(self) -> None:
        result = subprocess.CompletedProcess(["mypy"], 1, "", "")
        with patch("tools.mypy_ratchet._run", return_value=result):
            with self.assertRaisesRegex(RatchetError, "no parseable"):
                run_mypy(self.root)

    def test_run_mypy_ignores_notes_but_requires_errors(self) -> None:
        result = subprocess.CompletedProcess(
            ["mypy"],
            1,
            '{"file":"module.py","line":1,"column":0,"message":"Broken",'
            '"code":"assignment","severity":"error"}\n'
            '{"file":"module.py","line":1,"column":0,"message":"Context",'
            '"code":null,"severity":"note"}\n',
            "",
        )
        with patch("tools.mypy_ratchet._run", return_value=result):
            self.assertEqual(
                run_mypy(self.root),
                Counter({Diagnostic("module.py", "Broken", "assignment"): 1}),
            )


if __name__ == "__main__":
    unittest.main()
