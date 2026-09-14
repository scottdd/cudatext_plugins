"""Pure helpers for Tab Menu. No CudaText imports, so unit tests can run outside the editor."""

import math
import re


def format_size(size_bytes):
    size_bytes = int(size_bytes)
    if size_bytes == 0:
        return '0 B'
    units = ('B', 'kB', 'MB', 'GB', 'TB')
    i = min(int(math.floor(math.log(size_bytes, 1024))), len(units) - 1)
    value = round(size_bytes / math.pow(1024, i), 2)
    return '%s %s' % (value, units[i])


def count_words(text):
    return len(re.findall(r'\S+', text))


def is_non_ascii_char(ch):
    return ord(ch) > 127


def collect_nonascii_positions(lines):
    xs, ys, lens = [], [], []
    for row, line in enumerate(lines):
        for col, ch in enumerate(line):
            if is_non_ascii_char(ch):
                xs.append(col)
                ys.append(row)
                lens.append(1)
    return xs, ys, lens


def _next_from(lines, x, y):
    if not lines:
        return None
    if y < 0:
        y = 0
        x = -1
    if y >= len(lines):
        return None
    line = lines[y]
    start = max(x + 1, 0)
    for col in range(start, len(line)):
        if is_non_ascii_char(line[col]):
            return col, y
    for row in range(y + 1, len(lines)):
        line = lines[row]
        for col, ch in enumerate(line):
            if is_non_ascii_char(ch):
                return col, row
    return None


def _prev_from(lines, x, y):
    if not lines:
        return None
    if y >= len(lines):
        y = len(lines) - 1
        x = len(lines[y])
    if y < 0:
        return None
    line = lines[y]
    end = min(x, len(line))
    for col in range(end - 1, -1, -1):
        if is_non_ascii_char(line[col]):
            return col, y
    for row in range(y - 1, -1, -1):
        line = lines[row]
        for col in range(len(line) - 1, -1, -1):
            if is_non_ascii_char(line[col]):
                return col, row
    return None


def find_next_nonascii(lines, x, y, wrap=False):
    """Return (col, row, wrapped) or None. Search starts after (x, y)."""
    pos = _next_from(lines, x, y)
    if pos is not None:
        return pos[0], pos[1], False
    if wrap:
        pos = _next_from(lines, -1, 0)
        if pos is not None:
            return pos[0], pos[1], True
    return None


def find_prev_nonascii(lines, x, y, wrap=False):
    """Return (col, row, wrapped) or None. Search starts before (x, y)."""
    pos = _prev_from(lines, x, y)
    if pos is not None:
        return pos[0], pos[1], False
    if wrap and lines:
        last = len(lines) - 1
        pos = _prev_from(lines, len(lines[last]), last)
        if pos is not None:
            return pos[0], pos[1], True
    return None


def finder_wrap_enabled(finder_prop):
    """True when CudaText Find's Wrapped search (option O) is on.

    PROC_GET_FINDER_PROP returns op_wrap (persisted) and op_wrap_d (Find dialog).
    Prefer the dialog flag when present, matching the live Find toggle.
    """
    if not isinstance(finder_prop, dict):
        return False
    if 'op_wrap_d' in finder_prop:
        return bool(finder_prop['op_wrap_d'])
    return bool(finder_prop.get('op_wrap'))
