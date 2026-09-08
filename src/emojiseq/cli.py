"""Command-line entry point.

Usage:
    emojiseq [INPUT] [-o OUTPUT]

With no INPUT, reads from stdin. With no -o, writes to stdout. Both sides
are streamed, so this is fine on input too large to fit in memory.
"""

import argparse
import sys

from .formatter import format_stream


def _print_stats(stats, file):
    print("emojiseq stats:", file=file)
    print(f"  chars composed:      {stats.composed}", file=file)
    print(f"  joiners dropped:     {stats.joiners_dropped}", file=file)
    print(f"  joiners collapsed:   {stats.joiners_collapsed}", file=file)
    print(f"  selectors dropped:   {stats.selectors_dropped}", file=file)
    print(f"  selectors collapsed: {stats.selectors_collapsed}", file=file)


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
    outfile = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    try:
        stats = format_stream(infile, outfile)
    finally:
        if infile is not sys.stdin:
            infile.close()
        if outfile is not sys.stdout:
            outfile.close()

    if args.stats:
        _print_stats(stats, sys.stderr)


if __name__ == "__main__":
    main()
