"""Pure helpers for Tab Menu. No CudaText imports, so unit tests run outside the editor."""

import math
import os
import re
import tempfile
import time
from urllib.parse import quote


__version__ = '0.7.0'


class FileOpError(Exception):
    """A refused or failed file copy, write, or delete."""


def format_size(size_bytes):
    size_bytes = int(size_bytes)
    if size_bytes < 0:
        raise ValueError('size must be >= 0')
    if size_bytes == 0:
        return '0 B'
    units = ('B', 'kB', 'MB', 'GB', 'TB')
    i = min(int(math.floor(math.log(size_bytes, 1024))), len(units) - 1)
    value = round(size_bytes / math.pow(1024, i), 2)
    return '%s %s' % (value, units[i])


def count_words(text):
    if not text:
        return 0
    return len(re.findall(r'\S+', text))


def count_characters(text):
    """Unicode characters in the editor buffer, including one per line break."""
    if not text:
        return 0
    return len(text)


def format_status(on_disk, modified, read_only):
    if not on_disk:
        parts = ['unsaved']
    elif modified:
        parts = ['modified']
    else:
        parts = ['saved']
    if read_only:
        parts.append('read-only')
    return ', '.join(parts)


def format_line_endings(value):
    mapping = {
        'lf': 'LF (Unix)',
        'crlf': 'CRLF (Windows)',
        'cr': 'CR (classic Mac)',
    }
    if not value:
        return '(none)'
    return mapping.get(value, value)


def format_timestamp(mtime):
    if mtime is None:
        return '(none)'
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))


def format_labeled_rows(rows):
    """rows is a list of (label, value). None values are omitted."""
    visible = []
    for label, value in rows:
        if value is None:
            continue
        visible.append((str(label), str(value)))
    if not visible:
        return ''
    width = max(len(label) for label, _value in visible)
    return '\n'.join('%s: %s' % (label.ljust(width), value) for label, value in visible)


_FILE_INFO_FIELDS = (
    ('path', 'Full path'),
    ('filename', 'Filename'),
    ('status', 'Status'),
    ('encoding', 'Encoding'),
    ('line_endings', 'Line endings'),
    ('lexer', 'Lexer'),
    ('size_disk', 'Size on disk'),
    ('size_memory', 'Size in memory (UTF-8)'),
    ('lines', 'Lines'),
    ('words', 'Words'),
    ('characters', 'Characters'),
    ('modified', 'Last modified'),
)


def format_file_info(info):
    """Format a file-info dict. Missing keys and None values are omitted."""
    rows = []
    for key, label in _FILE_INFO_FIELDS:
        if key not in info:
            continue
        rows.append((label, info[key]))
    return format_labeled_rows(rows)


# CudaText dlg_proc colors are Lazarus TColor integers: 0x00BBGGRR.
# PROC_THEME_UI_DICT_GET returns those integers unchanged (see
# PyHelper_GetThemeDict_UI). html_color_to_int / TATHtmlColorParser.ParseTokenRGB
# pack #RRGGBB the same way. Green (#00FF00) survives a mistaken swap; amber
# (#E0A100) becomes blue (TColor 0xE0A100) if the bytes are left as 0xRRGGBB.
COLOR_NONE = 0x1FFFFFFF
COLOR_DEFAULT = 0x20000000
_TCOLOR_MAX = 0xFFFFFF

_BG_THEME_KEYS = ('ListBg', 'TreeBg', 'TabBg', 'SideBg', 'EdTextBg')
_TEXT_THEME_KEYS = ('ListFont', 'TreeFont', 'ButtonFont', 'TabFont', 'EdTextFont')

# fill, text, border, accent as #RRGGBB. Converted to TColor at use time.
_STATUS_HTML = {
    'dark': {
        'saved': ('#1B3D2F', '#9DDBB8', '#2F6B4A', '#3DDC97'),
        'modified': ('#3F3114', '#F0C36A', '#8C6A2E', '#E6A23C'),
        'unsaved': ('#333333', '#C8C8C8', '#555555', '#8E8E8E'),
        'readonly': ('#2E2E36', '#D0D0DC', '#555564', '#8E8E96'),
    },
    'light': {
        'saved': ('#E7F6EC', '#1E7A43', '#B7DEC6', '#1F8A4C'),
        'modified': ('#FBF4E4', '#8A5A00', '#E6D2A4', '#C4841D'),
        'unsaved': ('#F0F0F0', '#555555', '#D4D4D4', '#8A8A8A'),
        'readonly': ('#F3F3F6', '#4E4E5C', '#D8D8E0', '#7A7A88'),
    },
}

_FILE_SECTION_ROWS = (
    ('encoding', 'Encoding'),
    ('line_endings', 'Line endings'),
    ('lexer', 'Lexer'),
    ('size_disk', 'Size on disk'),
    ('size_memory', 'Size in memory'),
    ('modified', 'Last modified'),
)
_TEXT_SECTION_ROWS = (
    ('lines', 'Lines'),
    ('words', 'Words'),
    ('characters', 'Characters'),
)
_STATUS_LABELS = {
    'saved': 'Saved',
    'modified': 'Modified',
    'unsaved': 'Unsaved',
}

_DIALOG_W = 520
_DIALOG_MIN_W = 400
_MARGIN_X = 16
_RIGHT = 16
_ACCENT_W = 4
_TEXT_X = _ACCENT_W + 12
_FILENAME_Y = 12
_FILENAME_H = 22
_PATH_GAP = 2
_PATH_H = 22
_HEADER_PAD = 12
_TITLE_H = 16
_TITLE_GAP = 2
_ROW_H = 20
_ROW_PITCH = 22
_DIVIDER_GAP = 10
_DIVIDER_H = 1
_BUTTON_GAP = 12
_BUTTON_H = 26
_BUTTON_BOTTOM = 12
_CLOSE_W = 94
_COPY_W = 112
_BUTTON_SPACING = 8
_LABEL_W = 136
_PILL_H = 20
_PILL_GAP = 6
_VALUE_X = _TEXT_X + _LABEL_W + 8


def bgr_from_rgb(red, green, blue):
    """Pack 0-255 channels into a Lazarus TColor (0x00BBGGRR)."""
    return ((int(blue) & 0xFF) << 16) | ((int(green) & 0xFF) << 8) | (int(red) & 0xFF)


def rgb_from_bgr(color):
    """Unpack a TColor into (red, green, blue). Ignores the system-color byte."""
    color = int(color) & _TCOLOR_MAX
    red = color & 0xFF
    green = (color >> 8) & 0xFF
    blue = (color >> 16) & 0xFF
    return red, green, blue


def html_color_to_tcolor(value):
    """Convert '#RRGGBB' or '#RGB' to a CudaText TColor.

    Matches cudax_lib html_color_to_int: the source is RGB, the integer is BGR.
    '#00FF00' stays 0x00FF00. '#E0A100' becomes 0x00A1E0, not 0xE0A100.
    """
    text = str(value).strip()
    if text.startswith('#'):
        text = text[1:]
    if len(text) == 3:
        text = ''.join(ch * 2 for ch in text)
    if len(text) != 6:
        raise ValueError('expected #RRGGBB or #RGB')
    try:
        red = int(text[0:2], 16)
        green = int(text[2:4], 16)
        blue = int(text[4:6], 16)
    except ValueError:
        raise ValueError('expected #RRGGBB or #RGB')
    return bgr_from_rgb(red, green, blue)


def coerce_tcolor(value):
    """Return a 0x00BBGGRR integer, or None when the value is not a real color.

    Theme dict entries are {'color': int, 'desc': str}. Integers already in
    TColor form are passed through (not swapped a second time). clNone,
    clDefault, and system colors (negative, or above 0xFFFFFF) are rejected.
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, dict):
        if 'color' not in value:
            return None
        return coerce_tcolor(value.get('color'))
    if isinstance(value, int):
        if value < 0 or value > _TCOLOR_MAX:
            return None
        return value
    if isinstance(value, str):
        try:
            return html_color_to_tcolor(value)
        except ValueError:
            return None
    return None


def _srgb_channel(channel):
    value = channel / 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(color):
    """WCAG relative luminance of a TColor. 0 is black, 1 is white."""
    red, green, blue = rgb_from_bgr(color)
    return (
        0.2126 * _srgb_channel(red)
        + 0.7152 * _srgb_channel(green)
        + 0.0722 * _srgb_channel(blue)
    )


def is_dark_color(color, threshold=0.45):
    return relative_luminance(color) < threshold


def mix_tcolor(start, end, amount):
    """Blend two TColors in RGB space and pack the result back to BGR."""
    amount = max(0.0, min(1.0, float(amount)))
    red1, green1, blue1 = rgb_from_bgr(start)
    red2, green2, blue2 = rgb_from_bgr(end)

    def blend(left, right):
        return int(round(left + (right - left) * amount))

    return bgr_from_rgb(blend(red1, red2), blend(green1, green2), blend(blue1, blue2))


def _contrast_ratio(first, second):
    lighter = max(relative_luminance(first), relative_luminance(second))
    darker = min(relative_luminance(first), relative_luminance(second))
    return (lighter + 0.05) / (darker + 0.05)


def _theme_color(theme, keys):
    if not isinstance(theme, dict):
        return None
    for key in keys:
        if key not in theme:
            continue
        color = coerce_tcolor(theme.get(key))
        if color is not None:
            return color
    return None


def _readable_text(background, text):
    if text is None or _contrast_ratio(background, text) < 3.0:
        if is_dark_color(background):
            return html_color_to_tcolor('#F2F2F2')
        return html_color_to_tcolor('#1A1A1A')
    return text


def resolve_ui_palette(theme):
    """Colors for the file-info dialog from a PROC_THEME_UI_DICT_GET dict.

    Missing, empty, or partial themes fall back to a light neutral palette
    (CudaText's built-in UI theme is light). Returned integers are TColors.
    """
    background = _theme_color(theme, _BG_THEME_KEYS)
    if background is None:
        background = html_color_to_tcolor('#F6F6F6')
    text = _readable_text(background, _theme_color(theme, _TEXT_THEME_KEYS))
    return {
        'dark': is_dark_color(background),
        'background': background,
        'text': text,
        'muted': mix_tcolor(text, background, 0.42),
        'divider': mix_tcolor(background, text, 0.18),
    }


def file_info_status_colors(dark, kind):
    """TColor fill, text, border, and accent for one status badge."""
    group = 'dark' if dark else 'light'
    try:
        fill, text, border, accent = _STATUS_HTML[group][kind]
    except KeyError:
        raise ValueError('unknown status kind %r' % (kind,))
    return {
        'fill': html_color_to_tcolor(fill),
        'text': html_color_to_tcolor(text),
        'border': html_color_to_tcolor(border),
        'accent': html_color_to_tcolor(accent),
    }


def parse_file_status(status):
    """Return (kind, read_only) from format_status() text.

    kind is 'saved', 'modified', or 'unsaved'.
    """
    text = (status or '').strip().lower()
    read_only = 'read-only' in text
    if text.startswith('unsaved'):
        kind = 'unsaved'
    elif text.startswith('modified'):
        kind = 'modified'
    else:
        kind = 'saved'
    return kind, read_only


def file_info_badges(info):
    """Status pill, plus a Read-only pill when format_status appended it."""
    kind, read_only = parse_file_status((info or {}).get('status'))
    badges = [{'kind': kind, 'label': _STATUS_LABELS[kind]}]
    if read_only:
        badges.append({'kind': 'readonly', 'label': 'Read-only'})
    return badges


def parent_folder(path):
    """Directory portion of path, keeping the separators the path already uses.

    A bare filename returns ''. A Unix path at the root returns '/'.
    """
    text = '' if path is None else str(path).strip()
    if not text:
        return ''
    if '\\' in text and '/' not in text:
        parent = '\\'.join(text.split('\\')[:-1])
        return parent
    if '/' not in text:
        return ''
    parent = text.rsplit('/', 1)[0]
    if parent == '' and text.startswith('/'):
        return '/'
    return parent


def file_info_folder(info, unsaved_label='(Unsaved)'):
    """Muted path line: parent folder, or unsaved_label when the tab is unsaved."""
    info = info or {}
    kind, _read_only = parse_file_status(info.get('status'))
    if kind == 'unsaved':
        return unsaved_label
    path = '' if info.get('path') is None else str(info.get('path'))
    folder = parent_folder(path)
    if folder:
        return folder
    return path or unsaved_label


def _section_rows(info, fields):
    rows = []
    for key, label in fields:
        if key not in info:
            continue
        value = info[key]
        if value is None:
            continue
        rows.append((label, str(value)))
    return rows


def file_info_sections(info):
    """File and Text groups. Empty groups are omitted so the dialog has no blank band."""
    info = info or {}
    sections = []
    file_rows = _section_rows(info, _FILE_SECTION_ROWS)
    text_rows = _section_rows(info, _TEXT_SECTION_ROWS)
    if file_rows:
        sections.append({'key': 'file', 'title': 'File', 'rows': file_rows})
    if text_rows:
        sections.append({'key': 'text', 'title': 'Text', 'rows': text_rows})
    return sections


def _pill_width(label):
    return max(58, 8 * len(label) + 18)


def _place_pills(badges, width):
    right = width - _RIGHT
    placed = []
    for badge in reversed(badges):
        pill_w = _pill_width(badge['label'])
        x = right - pill_w
        placed.append((badge, x, pill_w))
        right = x - _PILL_GAP
    placed.reverse()
    return placed


def _header_height():
    return _FILENAME_Y + _FILENAME_H + _PATH_GAP + _PATH_H + _HEADER_PAD


def _colorpanel(name, x, y, w, h, fill, border=None, caption='', border_width=0, text=None, font_size=None):
    if border is None:
        border = fill
    if text is None:
        text = fill
    prop = {
        'name': name,
        'cap': caption,
        'x': x,
        'y': y,
        'w': w,
        'h': h,
        'color': fill,
        'font_color': text,
        'ex0': border_width,
        'ex1': fill,
        'ex2': text,
        'ex3': border,
    }
    if font_size:
        prop['font_size'] = font_size
    return {'type': 'colorpanel', 'prop': prop}


def _label(name, caption, x, y, w, h, palette, muted=False, style='', size=None, anchor_right=False):
    prop = {
        'name': name,
        'cap': caption,
        'x': x,
        'y': y,
        'w': w,
        'h': h,
        'autosize': False,
        'color': palette['background'],
        'font_color': palette['muted'] if muted else palette['text'],
    }
    if style:
        prop['font_style'] = style
    if size:
        prop['font_size'] = size
    if anchor_right:
        prop['a_r'] = ('', ']')
        prop['sp_r'] = _RIGHT
    return {'type': 'label', 'prop': prop}


def build_file_info_dialog(info, theme=None, captions=None):
    """Describe a theme-aware file-info dialog without touching CudaText.

    copy_text is exactly format_file_info(info). Colors in the control props
    are TColors (0xBBGGRR). The host sets DBORDER_SIZE, focuses btn_close
    (ex0 default button), and calls DLG_SCALE after creating the controls.
    """
    info = dict(info or {})
    captions = captions or {}
    close_cap = captions.get('close') or '&Close'
    copy_cap = captions.get('copy') or '&Copy Info'
    unsaved_label = captions.get('unsaved') or '(Unsaved)'

    palette = resolve_ui_palette(theme)
    badges = file_info_badges(info)
    sections = file_info_sections(info)
    kind = badges[0]['kind']
    status_colors = file_info_status_colors(palette['dark'], kind)
    folder = file_info_folder(info, unsaved_label=unsaved_label)
    filename = info.get('filename')
    if filename is None or str(filename).strip() == '':
        filename = unsaved_label
    else:
        filename = str(filename)

    width = _DIALOG_W
    header_h = _header_height()
    y = header_h
    section_layout = []
    for index, section in enumerate(sections):
        if index:
            y += _DIVIDER_GAP
            divider_y = y
            y += _DIVIDER_H + _DIVIDER_GAP
        else:
            divider_y = None
        title_y = y
        y += _TITLE_H + _TITLE_GAP
        row_ys = []
        for _label_text, _value in section['rows']:
            row_ys.append(y)
            y += _ROW_PITCH
        section_layout.append({
            'section': section,
            'divider_y': divider_y,
            'title_y': title_y,
            'row_ys': row_ys,
        })

    y += _BUTTON_GAP
    button_y = y
    height = button_y + _BUTTON_H + _BUTTON_BOTTOM

    pill_y = _FILENAME_Y + (_FILENAME_H - _PILL_H) // 2
    pills = _place_pills(badges, width)
    pill_left = pills[0][1]
    filename_w = max(48, pill_left - 10 - _TEXT_X)
    path_w = width - _TEXT_X - _RIGHT
    value_w = width - _VALUE_X - _RIGHT
    has_readonly = any(item['kind'] == 'readonly' for item in badges)

    controls = []
    close_x = width - _RIGHT - _CLOSE_W
    copy_x = close_x - _BUTTON_SPACING - _COPY_W
    controls.append({
        'type': 'button',
        'role': 'close',
        'prop': {
            'name': 'btn_close',
            'cap': close_cap,
            'a_l': None,
            'a_t': None,
            'a_r': ('', ']'),
            'a_b': ('', ']'),
            'sp_r': _RIGHT,
            'sp_b': _BUTTON_BOTTOM,
            'x': close_x,
            'y': button_y,
            'w': _CLOSE_W,
            'h': _BUTTON_H,
            'ex0': True,
        },
    })
    controls.append({
        'type': 'button',
        'role': 'copy',
        'prop': {
            'name': 'btn_copy',
            'cap': copy_cap,
            'a_l': None,
            'a_t': None,
            'a_r': ('btn_close', '['),
            'a_b': ('', ']'),
            'sp_r': _BUTTON_SPACING,
            'sp_b': _BUTTON_BOTTOM,
            'x': copy_x,
            'y': button_y,
            'w': _COPY_W,
            'h': _BUTTON_H,
        },
    })

    accent = _colorpanel(
        'accent',
        0,
        0,
        _ACCENT_W,
        header_h,
        status_colors['accent'],
        border=status_colors['accent'],
        border_width=0,
    )
    controls.append(accent)

    # Rightmost pill first so a later pill can anchor to it.
    for badge, x, pill_w in reversed(pills):
        colors = file_info_status_colors(palette['dark'], badge['kind'])
        name = 'pill_readonly' if badge['kind'] == 'readonly' else 'pill_status'
        pill = _colorpanel(
            name,
            x,
            pill_y,
            pill_w,
            _PILL_H,
            colors['fill'],
            border=colors['border'],
            caption=badge['label'],
            border_width=1,
            text=colors['text'],
            font_size=9,
        )
        pill['prop']['a_l'] = None
        if badge['kind'] == 'readonly' or not has_readonly:
            pill['prop']['a_r'] = ('', ']')
            pill['prop']['sp_r'] = _RIGHT
        else:
            pill['prop']['a_r'] = ('pill_readonly', '[')
            pill['prop']['sp_r'] = _PILL_GAP
        controls.append(pill)

    filename_ctl = _label(
        'filename',
        filename,
        _TEXT_X,
        _FILENAME_Y,
        filename_w,
        _FILENAME_H,
        palette,
        style='b',
        size=12,
    )
    filename_ctl['prop']['a_r'] = ('pill_status', '[')
    filename_ctl['prop']['sp_r'] = 10
    controls.append(filename_ctl)

    controls.append({
        'type': 'edit',
        'prop': {
            'name': 'path',
            'val': folder,
            'x': _TEXT_X,
            'y': _FILENAME_Y + _FILENAME_H + _PATH_GAP,
            'w': path_w,
            'h': _PATH_H,
            'a_r': ('', ']'),
            'sp_r': _RIGHT,
            'color': palette['background'],
            'font_color': palette['muted'],
            'font_size': 9,
            'ex0': True,
            'ex1': False,
            'ex2': False,
            'tab_stop': True,
        },
    })

    for block in section_layout:
        section = block['section']
        if block['divider_y'] is not None:
            divider = _colorpanel(
                'divider',
                _TEXT_X,
                block['divider_y'],
                width - _TEXT_X - _RIGHT,
                _DIVIDER_H,
                palette['divider'],
                border=palette['divider'],
                border_width=0,
            )
            divider['prop']['a_r'] = ('', ']')
            divider['prop']['sp_r'] = _RIGHT
            controls.append(divider)
        controls.append(_label(
            section['key'] + '_title',
            section['title'],
            _TEXT_X,
            block['title_y'],
            _LABEL_W,
            _TITLE_H,
            palette,
            muted=True,
            size=9,
        ))
        for row_index, ((label, value), row_y) in enumerate(zip(section['rows'], block['row_ys'])):
            controls.append(_label(
                '%s_label_%d' % (section['key'], row_index),
                label,
                _TEXT_X,
                row_y,
                _LABEL_W,
                _ROW_H,
                palette,
                muted=True,
            ))
            controls.append(_label(
                '%s_value_%d' % (section['key'], row_index),
                value,
                _VALUE_X,
                row_y,
                value_w,
                _ROW_H,
                palette,
                anchor_right=True,
            ))

    return {
        'width': width,
        'height': height,
        'min_width': _DIALOG_MIN_W,
        'min_height': height,
        'resizable': True,
        'focus': 'btn_close',
        'copy_text': format_file_info(info),
        'palette': palette,
        'accent': status_colors['accent'],
        'badges': badges,
        'sections': sections,
        'header': {
            'filename': filename,
            'folder': folder,
            'status': kind,
        },
        'controls': controls,
    }


def suggest_duplicate_name(filename, exists):
    """Return a basename stem_copy.ext, then stem_copy2.ext, that exists() rejects.

    exists is called with candidate basenames, not full paths.
    """
    stem, ext = os.path.splitext(filename)
    candidate = '%s_copy%s' % (stem, ext)
    if not exists(candidate):
        return candidate
    number = 2
    while number <= 10000:
        candidate = '%s_copy%d%s' % (stem, number, ext)
        if not exists(candidate):
            return candidate
        number += 1
    raise FileOpError('could not find a free duplicate name')


def clean_duplicate_basename(name):
    """A single file name in the same folder. Rejects paths."""
    cleaned = (name or '').strip()
    if not cleaned or cleaned in ('.', '..'):
        raise FileOpError('Enter a file name')
    if '/' in cleaned or '\\' in cleaned or os.path.basename(cleaned) != cleaned:
        raise FileOpError('Enter a file name in the same folder, not a path')
    return cleaned


def prepare_destination(path, overwrite=False):
    """Absolute file path that is safe to write. Raises FileOpError otherwise."""
    if path is None or not str(path).strip():
        raise FileOpError('empty path')
    dest = os.path.abspath(os.path.expanduser(str(path)))
    if os.path.isdir(dest):
        raise FileOpError('destination is a directory')
    parent = os.path.dirname(dest)
    if not parent or not os.path.isdir(parent):
        raise FileOpError('destination folder does not exist')
    if os.path.exists(dest):
        if os.path.islink(dest):
            if os.path.isdir(dest):
                raise FileOpError('destination is a directory')
        elif not os.path.isfile(dest):
            raise FileOpError('destination is not a file')
        if not overwrite:
            raise FileOpError('destination already exists')
    return dest


def safe_write_bytes(path, data, overwrite=False):
    """Write bytes via a temp file in the destination folder, then replace.

    The destination folder must already exist. Directories are never replaced.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise FileOpError('data must be bytes')
    dest = prepare_destination(path, overwrite=overwrite)
    parent = os.path.dirname(dest)
    fd, tmp = tempfile.mkstemp(prefix='.tabmenu-copy-', dir=parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(bytes(data))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, dest)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return dest


def safe_copy_file(src, dest, overwrite=False):
    """Byte-copy a regular file. Does not copy a path onto itself."""
    if not src or not str(src).strip():
        raise FileOpError('empty source path')
    source = os.path.abspath(os.path.expanduser(str(src)))
    if not os.path.isfile(source):
        raise FileOpError('source is not a file')
    target = os.path.abspath(os.path.expanduser(str(dest)))
    if os.path.normcase(source) == os.path.normcase(target):
        raise FileOpError('source and destination are the same file')
    with open(source, 'rb') as handle:
        data = handle.read()
    return safe_write_bytes(target, data, overwrite=overwrite)


def safe_delete_file(path):
    """Delete one regular file or a symlink to a file. Never deletes a directory."""
    if path is None or not str(path).strip():
        raise FileOpError('empty path')
    target = os.path.abspath(os.path.expanduser(str(path)))
    if not os.path.lexists(target):
        raise FileOpError('file does not exist')
    if os.path.isdir(target):
        raise FileOpError('refusing to delete a directory')
    if os.path.islink(target):
        os.remove(target)
        return target
    if not os.path.isfile(target):
        raise FileOpError('not a regular file')
    os.remove(target)
    return target


def first_path(value):
    """dlg_file may return a string, a list, or None."""
    if isinstance(value, (list, tuple)):
        return value[0] if value else ''
    return value or ''


_CODEC_ALIASES = {
    'utf8': ('utf-8', None),
    'utf-8': ('utf-8', None),
    'utf8_bom': ('utf-8', b'\xef\xbb\xbf'),
    'utf-8_bom': ('utf-8', b'\xef\xbb\xbf'),
    'utf16le': ('utf-16-le', None),
    'utf-16le': ('utf-16-le', None),
    'utf16le_bom': ('utf-16-le', b'\xff\xfe'),
    'utf-16le_bom': ('utf-16-le', b'\xff\xfe'),
    'utf16be': ('utf-16-be', None),
    'utf-16be': ('utf-16-be', None),
    'utf16be_bom': ('utf-16-be', b'\xfe\xff'),
    'utf-16be_bom': ('utf-16-be', b'\xfe\xff'),
    'utf32le': ('utf-32-le', None),
    'utf-32le': ('utf-32-le', None),
    'utf32le_bom': ('utf-32-le', b'\xff\xfe\x00\x00'),
    'utf-32le_bom': ('utf-32-le', b'\xff\xfe\x00\x00'),
    'utf32be': ('utf-32-be', None),
    'utf-32be': ('utf-32-be', None),
    'utf32be_bom': ('utf-32-be', b'\x00\x00\xfe\xff'),
    'utf-32be_bom': ('utf-32-be', b'\x00\x00\xfe\xff'),
    'iso88591': ('iso-8859-1', None),
    'iso8859-1': ('iso-8859-1', None),
    'iso88592': ('iso-8859-2', None),
    'iso885915': ('iso-8859-15', None),
    'mac': ('mac_roman', None),
}


def resolve_encoding(encoding):
    """Return (python_codec, bom_bytes_or_None) for a CudaText encoding short name."""
    name = (encoding or '').strip()
    if not name:
        return 'utf-8', None
    key = name.lower().replace(' ', '')
    if key in _CODEC_ALIASES:
        return _CODEC_ALIASES[key]
    try:
        import codecs
        codecs.lookup(name)
    except LookupError:
        raise FileOpError('unsupported encoding: %s' % encoding)
    return name, None


def encode_document(text, encoding, newline='keep'):
    """Encode editor text. newline is 'keep', 'lf', 'crlf', or 'cr'.

    'keep' writes the newlines already in text. The other modes first normalize
    any mix of CR/LF to the requested ending. A BOM is prepended for *_bom
    encodings when the encoded bytes do not already start with one.
    """
    if text is None:
        text = ''
    if newline == 'crlf':
        text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')
    elif newline == 'lf':
        text = text.replace('\r\n', '\n').replace('\r', '\n')
    elif newline == 'cr':
        text = text.replace('\r\n', '\n').replace('\n', '\r')
    elif newline != 'keep':
        raise FileOpError('unknown newline %r' % (newline,))
    codec, bom = resolve_encoding(encoding)
    try:
        data = text.encode(codec)
    except LookupError:
        raise FileOpError('unsupported encoding: %s' % encoding)
    except UnicodeEncodeError as exc:
        raise FileOpError('encoding %s cannot represent this text (%s)' % (encoding, exc.reason))
    if bom and not data.startswith(bom):
        data = bom + data
    return data


def platform_from_suffix(suffix):
    """Map CudaText PROC_GET_OS_SUFFIX to windows, macos, haiku, or linux.

    An empty suffix is Windows. Anything else (including a Linux suffix) is linux.
    """
    if suffix is None:
        suffix = ''
    suffix = str(suffix)
    if suffix == '':
        return 'windows'
    if suffix == '__mac':
        return 'macos'
    if suffix == '__haiku':
        return 'haiku'
    return 'linux'


def path_to_file_uri(path):
    absolute = os.path.abspath(path)
    return 'file://' + quote(absolute, safe='/')


def _attempt(argv, check=None, cwd=None, wait=False):
    item = {'argv': list(argv), 'wait': wait}
    if check:
        item['check'] = check
    if cwd:
        item['cwd'] = cwd
    return item


def reveal_attempts(platform, path):
    """Commands that select path in the OS file manager, in the order to try.

    Linux tries the FileManager1 D-Bus method first, then xdg-open on the folder.
    """
    path = os.path.abspath(path)
    folder = os.path.dirname(path) or path
    if platform == 'windows':
        return [_attempt(['explorer', '/select,' + path])]
    if platform == 'macos':
        return [_attempt(['open', '-R', path])]
    if platform == 'linux':
        uri = path_to_file_uri(path)
        return [
            _attempt(
                [
                    'dbus-send',
                    '--session',
                    '--type=method_call',
                    '--print-reply',
                    '--dest=org.freedesktop.FileManager1',
                    '/org/freedesktop/FileManager1',
                    'org.freedesktop.FileManager1.ShowItems',
                    'array:string:"%s"' % uri,
                    'string:""',
                ],
                check='dbus-send',
                wait=True,
            ),
            _attempt(
                [
                    'gdbus',
                    'call',
                    '--session',
                    '--dest',
                    'org.freedesktop.FileManager1',
                    '--object-path',
                    '/org/freedesktop/FileManager1',
                    '--method',
                    'org.freedesktop.FileManager1.ShowItems',
                    "['%s']" % uri,
                    "''",
                ],
                check='gdbus',
                wait=True,
            ),
            _attempt(['xdg-open', folder], check='xdg-open'),
        ]
    return []


def open_folder_attempts(platform, folder):
    folder = os.path.abspath(folder)
    if platform == 'windows':
        return [_attempt(['explorer', folder])]
    if platform == 'macos':
        return [_attempt(['open', folder])]
    if platform == 'linux':
        return [_attempt(['xdg-open', folder], check='xdg-open')]
    if platform == 'haiku':
        return [_attempt(['open', folder])]
    return []


def terminal_attempts(platform, folder):
    """Candidate terminals for folder. The first one whose program exists wins.

    Entries without 'check' are always available (cmd.exe on Windows).
    """
    folder = os.path.abspath(folder)
    if platform == 'windows':
        return [
            _attempt(['wt.exe', '-d', folder], check='wt.exe', cwd=folder),
            _attempt(['wt', '-d', folder], check='wt', cwd=folder),
            _attempt(['cmd.exe', '/c', 'start', '', 'cmd.exe', '/K'], cwd=folder),
        ]
    if platform == 'macos':
        return [_attempt(['open', '-a', 'Terminal', folder], cwd=folder)]
    if platform == 'linux':
        # Prefer terminals that take an explicit directory. A generic
        # x-terminal-emulator often ignores the process cwd when one window
        # is already open.
        specs = (
            ('gnome-terminal', ['--working-directory', folder]),
            ('kgx', ['--working-directory', folder]),
            ('konsole', ['--workdir', folder]),
            ('xfce4-terminal', ['--working-directory', folder]),
            ('mate-terminal', ['--working-directory', folder]),
            ('tilix', ['--working-directory', folder]),
            ('kitty', ['--directory', folder]),
            ('alacritty', ['--working-directory', folder]),
            ('wezterm', ['start', '--cwd', folder]),
            ('x-terminal-emulator', []),
            ('xterm', []),
        )
        return [
            _attempt([name] + args, check=name, cwd=folder)
            for name, args in specs
        ]
    return []


def first_available(attempts, is_available):
    """First attempt whose 'check' program exists. Missing 'check' is always usable."""
    for attempt in attempts:
        name = attempt.get('check')
        if name and not is_available(name):
            continue
        return attempt
    return None


def available_attempts(attempts, is_available):
    """Every attempt that can be launched, in order."""
    chosen = []
    for attempt in attempts:
        name = attempt.get('check')
        if name and not is_available(name):
            continue
        chosen.append(attempt)
    return chosen
