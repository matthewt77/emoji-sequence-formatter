"""Emoji property tables.

Ranges are copied from the Emoji_Modifier_Base property in Unicode's
emoji-data.txt (Unicode 15.1). They are inclusive (first, last) pairs,
sorted, so membership is a binary search. The table is small enough to live
in source; a full bundled copy of emoji-data.txt is only worth it once
something needs more than this one property.
"""

from bisect import bisect_right

SKIN_TONE_FIRST = 0x1F3FB  # light
SKIN_TONE_LAST = 0x1F3FF  # dark

_MODIFIER_BASE_RANGES = (
    (0x261D, 0x261D),
    (0x26F9, 0x26F9),
    (0x270A, 0x270D),
    (0x1F385, 0x1F385),
    (0x1F3C2, 0x1F3C4),
    (0x1F3C7, 0x1F3C7),
    (0x1F3CA, 0x1F3CC),
    (0x1F442, 0x1F443),
    (0x1F446, 0x1F450),
    (0x1F466, 0x1F469),
    (0x1F46B, 0x1F46E),
    (0x1F470, 0x1F478),
    (0x1F47C, 0x1F47C),
    (0x1F481, 0x1F483),
    (0x1F485, 0x1F487),
    (0x1F48F, 0x1F48F),
    (0x1F491, 0x1F491),
    (0x1F4AA, 0x1F4AA),
    (0x1F574, 0x1F575),
    (0x1F57A, 0x1F57A),
    (0x1F590, 0x1F590),
    (0x1F595, 0x1F596),
    (0x1F645, 0x1F647),
    (0x1F64B, 0x1F64F),
    (0x1F6A3, 0x1F6A3),
    (0x1F6B4, 0x1F6B6),
    (0x1F6C0, 0x1F6C0),
    (0x1F6CC, 0x1F6CC),
    (0x1F90C, 0x1F90C),
    (0x1F90F, 0x1F90F),
    (0x1F918, 0x1F91F),
    (0x1F926, 0x1F926),
    (0x1F930, 0x1F939),
    (0x1F93C, 0x1F93E),
    (0x1F977, 0x1F977),
    (0x1F9B5, 0x1F9B6),
    (0x1F9B8, 0x1F9B9),
    (0x1F9BB, 0x1F9BB),
    (0x1F9CD, 0x1F9CF),
    (0x1F9D1, 0x1F9DD),
    (0x1FAC3, 0x1FAC5),
    (0x1FAF0, 0x1FAF8),
)

_STARTS = tuple(first for first, _ in _MODIFIER_BASE_RANGES)


def is_skin_tone_modifier(ch):
    return SKIN_TONE_FIRST <= ord(ch) <= SKIN_TONE_LAST


def is_modifier_base(ch):
    """True if a skin-tone modifier may legally follow `ch`."""
    cp = ord(ch)
    i = bisect_right(_STARTS, cp) - 1
    return i >= 0 and cp <= _MODIFIER_BASE_RANGES[i][1]
