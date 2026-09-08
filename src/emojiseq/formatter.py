"""Core normalisation logic.

The interesting constraint here is memory: input can be arbitrarily large
(think a chat export or a log file full of reactions), so nothing in this
module reads the whole thing into a single string. Two buffering tricks
make that possible:

* Unicode composition (NFC) only ever needs to look at a base character
  plus the combining marks stuck to it, so we buffer one "cluster" at a
  time instead of the whole input.
* Zero-width joiners and variation selectors only need one character of
  lookback and one of lookahead to decide whether they're attached to
  anything real, so that pass holds at most one pending character.
"""

import unicodedata
from dataclasses import dataclass

ZERO_WIDTH_JOINER = "‍"
VARIATION_SELECTOR_15 = "︎"  # text presentation
VARIATION_SELECTOR_16 = "️"  # emoji presentation
VARIATION_SELECTORS = (VARIATION_SELECTOR_15, VARIATION_SELECTOR_16)

# Large enough that most inputs are read in one or two chunks, small enough
# that a genuinely huge file never lands in memory all at once.
_DEFAULT_CHUNK_SIZE = 65536


@dataclass
class Stats:
    """Counts of what a pass actually changed.

    Every field is a count of clusters or code points affected, not a
    count of input characters, so these stay meaningful regardless of
    how large the input was.
    """

    composed: int = 0
    joiners_dropped: int = 0
    joiners_collapsed: int = 0
    selectors_dropped: int = 0
    selectors_collapsed: int = 0

    @property
    def total_changes(self):
        return (
            self.composed
            + self.joiners_dropped
            + self.joiners_collapsed
            + self.selectors_dropped
            + self.selectors_collapsed
        )


def _iter_chars(readable, chunk_size=_DEFAULT_CHUNK_SIZE):
    """Yield one character at a time from a text-mode file-like object.

    Reading fixed-size chunks (rather than readline, which stalls on input
    with no newlines) is what keeps this bounded regardless of how the
    input is shaped. Text mode handles multi-byte characters split across
    chunk boundaries correctly, so this never has to worry about that.
    """
    while True:
        chunk = readable.read(chunk_size)
        if not chunk:
            return
        for ch in chunk:
            yield ch


def _iter_clusters(chars):
    """Group each base character with the combining marks that follow it."""
    cluster = []
    for ch in chars:
        if cluster and unicodedata.combining(ch) == 0:
            yield "".join(cluster)
            cluster = [ch]
        else:
            cluster.append(ch)
    if cluster:
        yield "".join(cluster)


def _iter_normalised_chars(chars, stats):
    for cluster in _iter_clusters(chars):
        normalised = unicodedata.normalize("NFC", cluster)
        if normalised != cluster:
            stats.composed += 1
        for ch in normalised:
            yield ch


def clean_joiners_and_selectors(chars, stats=None):
    """Drop zero-width joiners and variation selectors with nothing valid
    to attach to, and collapse runs of either into a single character.

    A joiner or selector with no emoji before it (start of input, or right
    after whitespace) is the most common way pasted emoji text ends up
    with visible tofu boxes or stray blank glyphs, so this is the one
    cleanup that matters most.
    """
    if stats is None:
        stats = Stats()

    held = None
    prev_emitted = None

    for ch in chars:
        if held is not None:
            if held == ZERO_WIDTH_JOINER:
                if ch == ZERO_WIDTH_JOINER:
                    stats.joiners_collapsed += 1
                    continue  # another joiner in a row: keep collapsing
                if ch.isspace():
                    held = None  # dangling joiner right before whitespace: drop it
                    stats.joiners_dropped += 1
                else:
                    yield held
                    prev_emitted = held
                    held = None
            else:
                if ch in VARIATION_SELECTORS:
                    held = ch  # a run of selectors: keep only the last one
                    stats.selectors_collapsed += 1
                    continue
                yield held
                prev_emitted = held
                held = None

        if ch == ZERO_WIDTH_JOINER or ch in VARIATION_SELECTORS:
            if prev_emitted is None or prev_emitted.isspace():
                # nothing before it to attach to: drop it
                if ch == ZERO_WIDTH_JOINER:
                    stats.joiners_dropped += 1
                else:
                    stats.selectors_dropped += 1
                continue
            held = ch
            continue

        yield ch
        prev_emitted = ch

    if held is not None:
        if held == ZERO_WIDTH_JOINER:
            stats.joiners_dropped += 1  # a trailing joiner is dropped
        else:
            yield held  # a trailing variation selector is fine


def format_stream(infile, outfile, chunk_size=_DEFAULT_CHUNK_SIZE):
    """Read text from `infile`, write the normalised version to `outfile`.

    Both are plain text-mode file-like objects. The whole pipeline is
    generators end to end, so memory use stays roughly constant no matter
    how large the input is.

    Returns a Stats object counting what was changed and how often.
    """
    stats = Stats()
    chars = _iter_chars(infile, chunk_size)
    normalised = _iter_normalised_chars(chars, stats)
    for ch in clean_joiners_and_selectors(normalised, stats):
        outfile.write(ch)
    return stats


def format_text(text):
    """Normalise a string already held in memory.

    Convenience wrapper for callers who don't have a stream handy; goes
    through the same code path as format_stream.
    """
    import io

    src = io.StringIO(text)
    dst = io.StringIO()
    format_stream(src, dst)
    return dst.getvalue()
