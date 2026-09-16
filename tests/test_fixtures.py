"""Regression tests against a small corpus of real-shaped messy input.

Unlike test_formatter.py, which isolates one defect per case, these fixtures
mix several problems in the same continuous stream the way an actual chat
export or spreadsheet dump would, so a fix for one defect can't accidentally
break another that happens to sit next to it.

Run with: python -m unittest discover
"""

import io
import pathlib
import unittest

from emojiseq.formatter import Stats, format_stream, format_text

FIXTURES = pathlib.Path(__file__).parent / "fixtures"

ZWJ = "‍"
VS16 = "️"
THUMBSUP = "\U0001f44d"
FIRE = "\U0001f525"
WOMAN = "\U0001f469"
GIRL = "\U0001f467"
BOY = "\U0001f466"


def read_fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


class ChatExportFixture(unittest.TestCase):
    def setUp(self):
        self.raw = read_fixture("chat_export.txt")

    def test_cleans_to_expected_output(self):
        expected = (
            "Alex: nice work today " + THUMBSUP + "\n"
            + "Sam: " + FIRE + " that demo was " + FIRE + ZWJ + FIRE + "\n"
            + "Jo: sending the whole family " + WOMAN + ZWJ + GIRL + ZWJ + BOY + " your way\n"
            + "Alex: café con leche, anyone?\n"
        )
        self.assertEqual(format_text(self.raw), expected)

    def test_reports_expected_stats(self):
        src = io.StringIO(self.raw)
        dst = io.StringIO()
        stats = format_stream(src, dst)
        self.assertEqual(
            stats,
            Stats(composed=1, joiners_dropped=2, joiners_collapsed=2),
        )

    def test_idempotent(self):
        once = format_text(self.raw)
        self.assertEqual(format_text(once), once)


class SpreadsheetExportFixture(unittest.TestCase):
    def setUp(self):
        self.raw = read_fixture("spreadsheet_export.txt")

    def test_cleans_to_expected_output(self):
        expected = (
            "status,note\n"
            + "done,shipped " + FIRE + "\n"
            + "blocked,waiting on " + THUMBSUP + " review\n"
        )
        self.assertEqual(format_text(self.raw), expected)

    def test_reports_expected_stats(self):
        src = io.StringIO(self.raw)
        dst = io.StringIO()
        stats = format_stream(src, dst)
        self.assertEqual(
            stats,
            Stats(joiners_dropped=2, joiners_collapsed=1, selectors_dropped=1),
        )

    def test_idempotent(self):
        once = format_text(self.raw)
        self.assertEqual(format_text(once), once)


if __name__ == "__main__":
    unittest.main()
