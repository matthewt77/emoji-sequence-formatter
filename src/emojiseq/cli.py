"""Command-line entry point.

Usage:
    emojiseq [INPUT] [-o OUTPUT]

With no INPUT, reads from stdin. With no -o, writes to stdout. Both sides
are streamed, so this is fine on input too large to fit in memory.
"""

import argparse
import sys

from .formatter import format_stream


def main(argv=None):
    parser = argparse.ArgumentParser(prog="emojiseq", description=__doc__)
    parser.add_argument("input", nargs="?", help="input file (default: stdin)")
    parser.add_argument("-o", "--output", help="output file (default: stdout)")
    args = parser.parse_args(argv)

    infile = open(args.input, "r", encoding="utf-8") if args.input else sys.stdin
    outfile = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    try:
        format_stream(infile, outfile)
    finally:
        if infile is not sys.stdin:
            infile.close()
        if outfile is not sys.stdout:
            outfile.close()


if __name__ == "__main__":
    main()
