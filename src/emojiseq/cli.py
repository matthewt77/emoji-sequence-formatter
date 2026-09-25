"""Command-line entry point.

Usage:
    emojiseq [INPUT] [-o OUTPUT]

With no INPUT, reads from stdin. With no -o, writes to stdout. Both sides
are streamed, so this is fine on input too large to fit in memory.
"""

import argparse
import os
import sys
import tempfile

from .formatter import format_stream


def _print_stats(stats, file):
    print("emojiseq stats:", file=file)
    print(f"  chars composed:      {stats.composed}", file=file)
    print(f"  joiners dropped:     {stats.joiners_dropped}", file=file)
    print(f"  joiners collapsed:   {stats.joiners_collapsed}", file=file)
    print(f"  selectors dropped:   {stats.selectors_dropped}", file=file)
    print(f"  selectors collapsed: {stats.selectors_collapsed}", file=file)


def _same_path(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="emojiseq", description=__doc__)
    parser.add_argument("input", nargs="?", help="input file (default: stdin)")
    parser.add_argument("-o", "--output", help="output file (default: stdout)")
    parser.add_argument(
        "--stats",
        action="store_true",
        help="print a summary of what was changed, and how often, to stderr",
    )
    args = parser.parse_args(argv)

    infile = open(args.input, "r", encoding="utf-8") if args.input else sys.stdin

    # -o opens its target in "w" mode immediately, which truncates the file
    # right away. If that target is the same path as the input, the infile
    # handle above would then read back nothing, since format_stream reads
    # it lazily in chunks rather than all at once. Route the in-place case
    # through a temp file in the same directory and swap it in afterwards,
    # so the original is only replaced once it's been fully read.
    in_place = args.input and args.output and _same_path(args.input, args.output)
    tmp_path = None
    if in_place:
        out_dir = os.path.dirname(os.path.abspath(args.output)) or "."
        tmp_fd, tmp_path = tempfile.mkstemp(dir=out_dir, prefix=".emojiseq-", suffix=".tmp")
        outfile = os.fdopen(tmp_fd, "w", encoding="utf-8")
    else:
        outfile = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout

    try:
        stats = format_stream(infile, outfile)
    except Exception:
        if tmp_path:
            outfile.close()
            os.remove(tmp_path)
        raise
    finally:
        if infile is not sys.stdin:
            infile.close()
        if outfile is not sys.stdout:
            outfile.close()

    if in_place:
        os.replace(tmp_path, args.output)

    if args.stats:
        _print_stats(stats, sys.stderr)


if __name__ == "__main__":
    main()
