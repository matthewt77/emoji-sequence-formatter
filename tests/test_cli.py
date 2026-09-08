"""Run with: python -m unittest discover"""

import contextlib
import io
import os
import sys
import tempfile
import unittest

from emojiseq.cli import main

ZWJ = "‍"
FIRE = "\U0001f525"


class MainFileArgs(unittest.TestCase):
    def test_reads_input_file_writes_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            in_path = os.path.join(tmp, "in.txt")
            out_path = os.path.join(tmp, "out.txt")
            with open(in_path, "w", encoding="utf-8") as f:
                f.write(ZWJ + FIRE)

            main([in_path, "-o", out_path])

            with open(out_path, encoding="utf-8") as f:
                self.assertEqual(f.read(), FIRE)

    def test_missing_input_file_raises(self):
        # A missing input file should surface the real error rather than
        # being masked by the open/close bookkeeping around stdin.
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "does-not-exist.txt")
            with self.assertRaises(FileNotFoundError):
                main([missing])


class MainStdStreams(unittest.TestCase):
    def run_main_with_stdin(self, argv, stdin_text):
        real_stdin = sys.stdin
        sys.stdin = io.StringIO(stdin_text)
        try:
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                main(argv)
            return captured.getvalue()
        finally:
            sys.stdin = real_stdin

    def test_stdin_to_stdout(self):
        result = self.run_main_with_stdin([], FIRE + ZWJ * 3 + FIRE)
        self.assertEqual(result, FIRE + ZWJ + FIRE)

    def test_stdin_to_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "out.txt")
            self.run_main_with_stdin(["-o", out_path], FIRE + ZWJ)
            with open(out_path, encoding="utf-8") as f:
                self.assertEqual(f.read(), FIRE)

    def test_stats_flag_reports_to_stderr_not_stdout(self):
        real_stdin = sys.stdin
        sys.stdin = io.StringIO(FIRE + ZWJ * 3 + FIRE)
        try:
            captured_out = io.StringIO()
            captured_err = io.StringIO()
            with contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
                main(["--stats"])
        finally:
            sys.stdin = real_stdin

        self.assertEqual(captured_out.getvalue(), FIRE + ZWJ + FIRE)
        self.assertIn("joiners collapsed:   2", captured_err.getvalue())


if __name__ == "__main__":
    unittest.main()
