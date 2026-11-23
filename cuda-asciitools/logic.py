"""Pure helpers for ASCII Tools. No CudaText imports, so unit tests run outside the editor."""

import unicodedata

__version__ = '0.1.0'


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


def normalize_selection(x, y, x2, y2):
    """Return (x1, y1, x2, y2) with the start before the end, or None.

    CudaText carets use x2 < 0 when there is no selection. An empty range
    (caret and anchor on the same character) is not a selection.
    """
    if x2 is None or y2 is None or x2 < 0 or y2 < 0:
        return None
    if (y2, x2) == (y, x):
        return None
    if (y2, x2) < (y, x):
        x, y, x2, y2 = x2, y2, x, y
    return (x, y, x2, y2)


def selections_from_carets(carets):
    """Normalized selections from CudaText get_carets() tuples, top to bottom."""
    spans = []
    for caret in carets or []:
        if not caret or len(caret) < 4:
            continue
        span = normalize_selection(caret[0], caret[1], caret[2], caret[3])
        if span:
            spans.append(span)
    spans.sort(key=lambda span: (span[1], span[0]))
    return spans


def _entry(row, col, ch):
    return {
        'line': row + 1,
        'column': col + 1,
        'char': ch,
        'codepoint': 'U+%04X' % ord(ch),
        'name': unicodedata.name(ch, '<unnamed>'),
    }


def collect_nonascii_entries(lines, span=None):
    """Non-ASCII characters as dicts with 1-based line and column.

    span is (x1, y1, x2, y2) in 0-based editor coordinates, or None for the
    whole document. Columns count Python characters (one per code point).
    """
    entries = []
    if not lines:
        return entries
    if span is None:
        x1, y1, x2, y2 = 0, 0, len(lines[-1]), len(lines) - 1
    else:
        x1, y1, x2, y2 = span
    last = len(lines) - 1
    y1 = max(0, min(y1, last))
    y2 = max(0, min(y2, last))
    if y2 < y1:
        return entries
    for row in range(y1, y2 + 1):
        line = lines[row]
        start = x1 if row == y1 else 0
        end = x2 if row == y2 else len(line)
        if start < 0:
            start = 0
        if end > len(line):
            end = len(line)
        if start >= end:
            continue
        for col in range(start, end):
            ch = line[col]
            if is_non_ascii_char(ch):
                entries.append(_entry(row, col, ch))
    return entries


def collect_nonascii_in_spans(lines, spans):
    """Entries inside spans. An empty span list scans the whole document.

    Overlapping spans are reported once, in reading order.
    """
    if not spans:
        return collect_nonascii_entries(lines, None)
    seen = set()
    entries = []
    ordered = sorted(spans, key=lambda span: (span[1], span[0]))
    for span in ordered:
        for entry in collect_nonascii_entries(lines, span):
            key = (entry['line'], entry['column'])
            if key in seen:
                continue
            seen.add(key)
            entries.append(entry)
    return entries


def _char_cell(ch):
    category = unicodedata.category(ch)
    if category.startswith('C') or ch.isspace() or not ch.isprintable():
        return '<U+%04X>' % ord(ch)
    return ch


def format_nonascii_report(entries, scope='whole document'):
    """Aligned text report plus a summary count. scope is a short label."""
    header = ('Line', 'Col', 'Char', 'Code point', 'Name')
    body = [
        (
            str(entry['line']),
            str(entry['column']),
            _char_cell(entry['char']),
            entry['codepoint'],
            entry['name'],
        )
        for entry in entries
    ]
    widths = [len(cell) for cell in header]
    for row in body:
        for index, cell in enumerate(row):
            if len(cell) > widths[index]:
                widths[index] = len(cell)

    def paint(row):
        return '  '.join(cell.ljust(widths[index]) for index, cell in enumerate(row)).rstrip()

    lines_out = ['Scope: %s' % scope, '']
    if body:
        lines_out.append(paint(header))
        lines_out.append(paint(tuple('-' * width for width in widths)))
        lines_out.extend(paint(row) for row in body)
        lines_out.append('')
    count = len(entries)
    noun = 'character' if count == 1 else 'characters'
    lines_out.append('%d non-ASCII %s' % (count, noun))
    return '\n'.join(lines_out)


def strip_nonascii(text):
    """Drop every non-ASCII character. Newlines and plain ASCII stay."""
    if not text:
        return text
    return ''.join(ch for ch in text if not is_non_ascii_char(ch))


# Unicode punctuation and spaces that have a plain ASCII stand-in.
# Accented letters are intentionally absent: this is not transliteration.
_PUNCT_MAP = {
    # Smart single quotes and single angle quotes.
    '\u2018': "'",
    '\u2019': "'",
    '\u201a': "'",
    '\u201b': "'",
    '\u2039': "'",
    '\u203a': "'",
    # Smart double quotes and double angle quotes.
    '\u201c': '"',
    '\u201d': '"',
    '\u201e': '"',
    '\u201f': '"',
    '\u00ab': '"',
    '\u00bb': '"',
    # Primes.
    '\u2032': "'",
    '\u2033': '"',
    '\u2034': "'''",
    '\u2035': "'",
    '\u2036': '"',
    '\u2037': "'''",
    # Hyphens and dashes. Em dash and horizontal bar become two hyphens.
    '\u2010': '-',
    '\u2011': '-',
    '\u2012': '-',
    '\u2013': '-',
    '\u2014': '--',
    '\u2015': '--',
    '\u2212': '-',
    # Ellipsis.
    '\u2026': '...',
    # Unusual spaces become a normal space.
    '\u00a0': ' ',
    '\u2000': ' ',
    '\u2001': ' ',
    '\u2002': ' ',
    '\u2003': ' ',
    '\u2004': ' ',
    '\u2005': ' ',
    '\u2006': ' ',
    '\u2007': ' ',
    '\u2008': ' ',
    '\u2009': ' ',
    '\u200a': ' ',
    '\u202f': ' ',
    '\u205f': ' ',
    '\u3000': ' ',
    # Zero-width characters are removed (they have no visible ASCII form).
    '\u200b': '',
    '\u200c': '',
    '\u200d': '',
    '\u2060': '',
    '\ufeff': '',
    # Bullets used as list markers.
    '\u2022': '-',
    '\u2023': '-',
    '\u2043': '-',
    '\u2219': '-',
    '\u25aa': '-',
    '\u25cf': '-',
    '\u25e6': '-',
}


def normalize_punctuation(text):
    """Map common Unicode punctuation and spaces to ASCII.

    Letters with accents are left unchanged. Zero-width spaces are removed.
    """
    if not text:
        return text
    return ''.join(_PUNCT_MAP.get(ch, ch) for ch in text)
