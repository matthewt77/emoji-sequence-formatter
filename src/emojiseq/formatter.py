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

ZERO_WIDTH_JOINER = "‍"
VARIATION_SELECTOR_15 = "︎"  # text presentation
VARIATION_SELECTOR_16 = "️"  # emoji presentation
VARIATION_SELECTORS = (VARIATION_SELECTOR_15, VARIATION_SELECTOR_16)

# Large enough that most inputs are read in one or two chunks, small enough
# that a genuinely huge file never lands in memory all at once.
_DEFAULT_CHUNK_SIZE = 65536


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


def _iter_normalised_chars(chars):
    for cluster in _iter_clusters(chars):
        for ch in unicodedata.normalize("NFC", cluster):
            yield ch


def clean_joiners_and_selectors(chars):
    """Drop zero-width joiners and variation selectors with nothing valid
    to attach to, and collapse runs of either into a single character.

    A joiner or selector with no emoji before it (start of input, or right
    after whitespace) is the most common way pasted emoji text ends up
    with visible tofu boxes or stray blank glyphs, so this is the one
    cleanup that matters most.
    """
    held = None
    prev_emitted = None

    for ch in chars:
        if held is not None:
            if held == ZERO_WIDTH_JOINER:
                if ch == ZERO_WIDTH_JOINER:
                    continue  # another joiner in a row: keep collapsing
                if ch.isspace():
                    held = None  # dangling joiner right before whitespace: drop it
                else:
                    yield held
                    prev_emitted = held
                    held = None
            else:
                if ch in VARIATION_SELECTORS:
                    held = ch  # a run of selectors: keep only the last one
                    continue
                yield held
                prev_emitted = held
                held = None

        if ch == ZERO_WIDTH_JOINER or ch in VARIATION_SELECTORS:
            if prev_emitted is None or prev_emitted.isspace():
                continue  # nothing before it to attach to: drop it
            held = ch
            continue

        yield ch
        prev_emitted = ch

    if held is not None and held != ZERO_WIDTH_JOINER:
        yield held  # a trailing variation selector is fine; a trailing joiner is not


def format_stream(infile, outfile, chunk_size=_DEFAULT_CHUNK_SIZE):
    """Read text from `infile`, write the normalised version to `outfile`.

    Both are plain text-mode file-like objects. The whole pipeline is
    generators end to end, so memory use stays roughly constant no matter
    how large the input is.
    """
    chars = _iter_chars(infile, chunk_size)
    normalised = _iter_normalised_chars(chars)
    for ch in clean_joiners_and_selectors(normalised):
        outfile.write(ch)


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
