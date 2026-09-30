"""Normalise messy emoji sequences in text."""

from .formatter import (
    Stats,
    clean_joiners_and_selectors,
    drop_orphan_modifiers,
    format_stream,
    format_text,
)

__all__ = [
    "format_stream",
    "format_text",
    "clean_joiners_and_selectors",
    "drop_orphan_modifiers",
    "Stats",
]
__version__ = "0.1.0"
