"""Run with: python -m unittest discover"""

import io
import unittest

from emojiseq.formatter import clean_joiners_and_selectors, format_stream, format_text

ZWJ = "‍"
VS15 = "︎"
VS16 = "️"
FIRE = "\U0001f525"
HEART = "❤"


class CleanJoinersAndSelectors(unittest.TestCase):
    def run_clean(self, text):
        return "".join(clean_joiners_and_selectors(text))

    def test_collapses_repeated_joiners(self):
        self.assertEqual(self.run_clean(FIRE + ZWJ * 3 + FIRE), FIRE + ZWJ + FIRE)

    def test_drops_leading_joiner(self):
        self.assertEqual(self.run_clean(ZWJ + FIRE), FIRE)

    def test_drops_joiner_before_whitespace(self):
        self.assertEqual(self.run_clean(FIRE + ZWJ + " "), FIRE + " ")

    def test_drops_trailing_joiner_at_end_of_input(self):
        self.assertEqual(self.run_clean(FIRE + ZWJ), FIRE)

    def test_keeps_last_of_a_selector_run(self):
        self.assertEqual(self.run_clean(HEART + VS15 + VS16), HEART + VS16)

    def test_drops_orphan_leading_selector(self):
        self.assertEqual(self.run_clean(VS16 + FIRE), FIRE)


class FormatText(unittest.TestCase):
    def test_composes_combining_accent(self):
        decomposed = "cafe" + "́"  # "e" followed by a combining acute accent
        precomposed = "café"
        self.assertEqual(format_text(decomposed), precomposed)

    def test_leaves_well_formed_sequences_alone(self):
        family = "\U0001f469" + ZWJ + "\U0001f467" + ZWJ + "\U0001f466"
        self.assertEqual(format_text(family), family)


class FormatStream(unittest.TestCase):
    def test_correct_across_chunk_boundaries(self):
        family = "\U0001f469" + ZWJ + "\U0001f467" + ZWJ + "\U0001f466"
        src = io.StringIO(family)
        dst = io.StringIO()
        format_stream(src, dst, chunk_size=1)  # force a read per character
        self.assertEqual(dst.getvalue(), family)


if __name__ == "__main__":
    unittest.main()
