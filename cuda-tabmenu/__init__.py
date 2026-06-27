import math
import os
import re
import subprocess

__version__ = '0.5'

from cudatext import *
from cudax_lib import get_translation

from .anyascii import anyascii as transliterate_to_ascii

_ = get_translation(__file__)

CAP_INFO = _('Info')
CAP_OPEN_PATH = _('Open Path')
CAP_UNSAVED = _('(unsaved)')
CAP_NONE = _('(none)')
CAP_DIALOG = _('Tab Info')
STATUS_UNSAVED = _('unsaved')
STATUS_SAVED = _('saved')
STATUS_MODIFIED = _('modified')

CAP_NONASCII = _('Non-ASCII')
CAP_HIGHLIGHT_NONASCII = _('Highlight Non-ASCII')
CAP_UNHIGHLIGHT_NONASCII = _('Un-highlight Non-ASCII')
CAP_NEXT_NONASCII = _('Next Non-ASCII Character')
CAP_PREV_NONASCII = _('Previous Non-ASCII Character')
CAP_TRANSLITERATE_ASCII = _('Transliterate to ASCII')

NONASCII_MARK_TAG = 88001
NONASCII_HIGHLIGHT_STYLE = dict(
    color_bg='#FFE8A0',
    border_down=4,
)
SEARCH_MENU_TAG = 'cuda_tabmenu_search'

OS_SUFFIX = app_proc(PROC_GET_OS_SUFFIX, '')


def format_size(size_bytes):
    size_bytes = int(size_bytes)
    if size_bytes == 0:
        return '0 B'
    units = ('B', 'kB', 'MB', 'GB', 'TB')
    i = min(int(math.floor(math.log(size_bytes, 1024))), len(units) - 1)
    value = round(size_bytes / math.pow(1024, i), 2)
    return '%s %s' % (value, units[i])


def is_saved_file(filepath):
    return bool(filepath) and os.path.isfile(filepath)


def is_text_document(ed):
    return ed.get_prop(PROP_KIND) == 'text'


def count_words(text):
    return len(re.findall(r'\S+', text))


def get_file_status(ed):
    if not is_saved_file(ed.get_filename()):
        return STATUS_UNSAVED
    if ed.get_prop(PROP_MODIFIED):
        return STATUS_MODIFIED
    return STATUS_SAVED


def get_encoding(ed):
    enc = ed.get_prop(PROP_ENC)
    return enc if enc else CAP_NONE


def get_lexer(ed):
    lex = ed.get_prop(PROP_LEXER_FILE)
    if not lex:
        return CAP_NONE
    if lex.endswith(' ^'):
        lex = lex[:-2]
    return lex


def is_non_ascii_char(ch):
    return ord(ch) > 127


def collect_nonascii_positions(ed):
    xs, ys, lens = [], [], []
    for row in range(ed.get_line_count()):
        line = ed.get_text_line(row)
        for col, ch in enumerate(line):
            if is_non_ascii_char(ch):
                xs.append(col)
                ys.append(row)
                lens.append(1)
    return xs, ys, lens


def find_next_nonascii(ed, x, y):
    line = ed.get_text_line(y)
    for col in range(x + 1, len(line)):
        if is_non_ascii_char(line[col]):
            return col, y
    for row in range(y + 1, ed.get_line_count()):
        line = ed.get_text_line(row)
        for col, ch in enumerate(line):
            if is_non_ascii_char(ch):
                return col, row
    return None


def find_prev_nonascii(ed, x, y):
    line = ed.get_text_line(y)
    for col in range(x - 1, -1, -1):
        if is_non_ascii_char(line[col]):
            return col, y
    for row in range(y - 1, -1, -1):
        line = ed.get_text_line(row)
        for col in range(len(line) - 1, -1, -1):
            if is_non_ascii_char(line[col]):
                return col, row
    return None


def highlight_nonascii(ed):
    ed.attr(MARKERS_DELETE_BY_TAG, NONASCII_MARK_TAG)
    xs, ys, lens = collect_nonascii_positions(ed)
    if xs:
        ed.attr(MARKERS_ADD_MANY, NONASCII_MARK_TAG, xs, ys, lens, **NONASCII_HIGHLIGHT_STYLE)
    return len(xs)


def unhighlight_nonascii(ed):
    ed.attr(MARKERS_DELETE_BY_TAG, NONASCII_MARK_TAG)


def goto_nonascii(ed, pos):
    if pos is None:
        return False
    col, row = pos
    ed.set_caret(col, row, col + 1, row)
    ed.focus()
    return True


def open_folder(folder):
    if not folder or not os.path.isdir(folder):
        msg_status(_('Folder not found: {}').format(folder))
        return

    try:
        if OS_SUFFIX == '':
            subprocess.Popen(['explorer', folder])
        elif OS_SUFFIX == '__mac':
            subprocess.Popen(['open', folder])
        elif OS_SUFFIX == '__haiku':
            msg_status(_('Open Path is not implemented for Haiku'))
        else:
            subprocess.Popen(['xdg-open', folder])
    except Exception as ex:
        msg_status(_('Error opening folder: {}').format(ex))


class Command:

    def __init__(self):
        self._tab_ed = None

    def on_tab_menu(self, ed_self):
        self._tab_ed = ed_self
        tab_id = menu_proc('tab', MENU_GET_PROP)['id']
        can_open_path = is_saved_file(ed_self.get_filename())

        self._set_menu_item(tab_id, CAP_INFO, 'cuda_tabmenu.menu_info', True)
        self._set_menu_item(tab_id, CAP_OPEN_PATH, 'cuda_tabmenu.menu_open_path', can_open_path)
        self._set_nonascii_submenu(tab_id, 'menu', is_text_document(ed_self))

    def on_init_plugins_menu(self, ed_self):
        self._install_search_menu()

    def _install_search_menu(self):
        items = menu_proc('top-sr', MENU_ENUM) or []
        existing = [item for item in items if item.get('tag') == SEARCH_MENU_TAG]
        if existing:
            parent_id = existing[0]['id']
            menu_proc(parent_id, MENU_CLEAR)
            self._fill_nonascii_submenu(parent_id, 'search')
            return
        menu_proc('top-sr', MENU_ADD, caption='-', tag=SEARCH_MENU_TAG + '_sep')
        parent_id = menu_proc('top-sr', MENU_ADD, caption=CAP_NONASCII, tag=SEARCH_MENU_TAG)
        self._fill_nonascii_submenu(parent_id, 'search')

    def _remove_menu_item(self, menu_id, caption):
        for item in menu_proc(menu_id, MENU_ENUM):
            if item.get('cap') == caption:
                menu_proc(item['id'], MENU_REMOVE)
                return True
        return False

    def _set_menu_item(self, tab_id, caption, command, enabled):
        self._remove_menu_item(tab_id, caption)
        item_id = menu_proc(tab_id, MENU_ADD, caption=caption, command=command)
        if not enabled:
            menu_proc(item_id, MENU_SET_ENABLED, command=False)

    def _set_nonascii_submenu(self, parent_id, cmd_prefix, enabled):
        self._remove_menu_item(parent_id, CAP_NONASCII)
        parent_id = menu_proc(parent_id, MENU_ADD, caption=CAP_NONASCII)
        if not enabled:
            menu_proc(parent_id, MENU_SET_ENABLED, command=False)
        self._fill_nonascii_submenu(parent_id, cmd_prefix, enabled)

    def _fill_nonascii_submenu(self, parent_id, cmd_prefix, enabled=True):
        submenu_items = [
            (CAP_HIGHLIGHT_NONASCII, f'cuda_tabmenu.{cmd_prefix}_highlight_nonascii'),
            (CAP_UNHIGHLIGHT_NONASCII, f'cuda_tabmenu.{cmd_prefix}_unhighlight_nonascii'),
            ('-', ''),
            (CAP_NEXT_NONASCII, f'cuda_tabmenu.{cmd_prefix}_next_nonascii'),
            (CAP_PREV_NONASCII, f'cuda_tabmenu.{cmd_prefix}_prev_nonascii'),
            ('-', ''),
            (CAP_TRANSLITERATE_ASCII, f'cuda_tabmenu.{cmd_prefix}_transliterate_ascii'),
        ]
        for caption, command in submenu_items:
            if caption == '-':
                menu_proc(parent_id, MENU_ADD, caption='-')
                continue
            item_id = menu_proc(parent_id, MENU_ADD, caption=caption, command=command)
            if not enabled:
                menu_proc(item_id, MENU_SET_ENABLED, command=False)

    def menu_info(self):
        ed = self._tab_ed
        if ed is None:
            return
        self._show_info_dialog(ed)

    def search_info(self):
        self._show_info_dialog(ed)

    def menu_open_path(self):
        ed = self._tab_ed
        if ed is None:
            return

        filepath = ed.get_filename()
        if not is_saved_file(filepath):
            return

        open_folder(os.path.dirname(os.path.abspath(filepath)))

    def _ed_text(self, ed):
        if ed is None or not is_text_document(ed):
            return None
        return ed

    def _do_highlight_nonascii(self, ed):
        ed = self._ed_text(ed)
        if ed is None:
            msg_status(_('Not a text document'))
            return
        count = highlight_nonascii(ed)
        msg_status(_('Highlighted {} non-ASCII character(s)').format(count))

    def _do_unhighlight_nonascii(self, ed):
        ed = self._ed_text(ed)
        if ed is None:
            msg_status(_('Not a text document'))
            return
        unhighlight_nonascii(ed)
        msg_status(_('Non-ASCII highlights removed'))

    def _do_next_nonascii(self, ed):
        ed = self._ed_text(ed)
        if ed is None:
            msg_status(_('Not a text document'))
            return
        x, y, x1, y1 = ed.get_carets()[0]
        if not goto_nonascii(ed, find_next_nonascii(ed, x, y)):
            msg_status(_('No more non-ASCII characters'))

    def _do_prev_nonascii(self, ed):
        ed = self._ed_text(ed)
        if ed is None:
            msg_status(_('Not a text document'))
            return
        x, y, x1, y1 = ed.get_carets()[0]
        if not goto_nonascii(ed, find_prev_nonascii(ed, x, y)):
            msg_status(_('No more non-ASCII characters'))

    def menu_highlight_nonascii(self):
        self._do_highlight_nonascii(self._tab_ed)

    def menu_unhighlight_nonascii(self):
        self._do_unhighlight_nonascii(self._tab_ed)

    def menu_next_nonascii(self):
        self._do_next_nonascii(self._tab_ed)

    def menu_prev_nonascii(self):
        self._do_prev_nonascii(self._tab_ed)

    def search_highlight_nonascii(self):
        self._do_highlight_nonascii(ed)

    def search_unhighlight_nonascii(self):
        self._do_unhighlight_nonascii(ed)

    def search_next_nonascii(self):
        self._do_next_nonascii(ed)

    def search_prev_nonascii(self):
        self._do_prev_nonascii(ed)

    def _do_transliterate_ascii(self, ed):
        ed = self._ed_text(ed)
        if ed is None:
            msg_status(_('Not a text document'))
            return
        if msg_box(
            _('Transliterate all non-ASCII characters to ASCII in this document?'),
            MB_OKCANCEL + MB_ICONQUESTION,
        ) != ID_OK:
            return

        text = ed.get_text_all()
        new_text = transliterate_to_ascii(text)
        if new_text == text:
            msg_status(_('No non-ASCII characters found'))
            return

        ed.set_text_all(new_text)
        msg_status(_('Transliterated to ASCII'))

    def menu_transliterate_ascii(self):
        self._do_transliterate_ascii(self._tab_ed)

    def search_transliterate_ascii(self):
        self._do_transliterate_ascii(ed)

    def _build_info_text(self, ed):
        filepath = ed.get_filename()
        saved = is_saved_file(filepath)
        modified = ed.get_prop(PROP_MODIFIED)

        if saved:
            file_path = os.path.abspath(filepath)
            file_name = os.path.basename(file_path)
        else:
            file_path = CAP_UNSAVED
            title = ed.get_prop(PROP_TAB_TITLE).lstrip('*')
            file_name = title or CAP_UNSAVED

        lines = [
            _('File path: {}').format(file_path),
            _('File name: {}').format(file_name),
            _('Status: {}').format(get_file_status(ed)),
            _('Encoding: {}').format(get_encoding(ed)),
            _('Lexer: {}').format(get_lexer(ed)),
        ]

        if saved:
            lines.append(_('Size on disk: {}').format(format_size(os.path.getsize(filepath))))

        if modified or not saved:
            text = ed.get_text_all()
            lines.append(_('Size in memory: {}').format(format_size(len(text.encode('utf-8')))))

        if is_text_document(ed):
            line_count = ed.get_line_count()
            lines.append(_('Line count: {}').format(line_count))
            if modified or not saved:
                word_count = count_words(text)
            else:
                word_count = count_words(ed.get_text_all())
            lines.append(_('Word count: {}').format(word_count))

        return '\n'.join(lines)

    def _show_info_dialog(self, ed):
        text = self._build_info_text(ed)

        w = 560
        h = 320
        dlg = dlg_proc(0, DLG_CREATE)
        dlg_proc(dlg, DLG_PROP_SET, prop={
            'cap': CAP_DIALOG,
            'w': w,
            'h': h,
            'w_min': 360,
            'h_min': 180,
            'border': DBORDER_SIZE,
        })

        btn = dlg_proc(dlg, DLG_CTL_ADD, prop='button')
        dlg_proc(dlg, DLG_CTL_PROP_SET, index=btn, prop={
            'name': 'btn_ok',
            'cap': _('&OK'),
            'a_l': None,
            'a_t': None,
            'a_r': ('', ']'),
            'a_b': ('', ']'),
            'sp_a': 6,
            'x': w - 100,
            'y': h - 6 - 25,
            'w': 94,
            'on_change': self._info_dialog_close,
            'ex0': True,
        })

        memo = dlg_proc(dlg, DLG_CTL_ADD, prop='memo')
        dlg_proc(dlg, DLG_CTL_PROP_SET, index=memo, prop={
            'name': 'memo_info',
            'val': text,
            'a_r': ('btn_ok', ']'),
            'a_b': ('btn_ok', '['),
            'x': 6,
            'y': 6,
            'w': w - 12,
            'h': h - 6 - 25 - 12,
            'ex0': True,
            'ex1': True,
        })

        dlg_proc(dlg, DLG_CTL_FOCUS, name='btn_ok')
        dlg_proc(dlg, DLG_SCALE)
        dlg_proc(dlg, DLG_SHOW_MODAL)
        dlg_proc(dlg, DLG_FREE)

    def _info_dialog_close(self, id_dlg, id_ctl, data='', info=''):
        dlg_proc(id_dlg, DLG_HIDE)