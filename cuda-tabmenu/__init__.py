import os
import subprocess
import sys
import traceback

__version__ = '0.6.2'

from cudatext import *
from cudax_lib import get_translation

from .anyascii import anyascii as transliterate_to_ascii
from .logic import (
    collect_nonascii_positions,
    count_words,
    find_next_nonascii,
    find_prev_nonascii,
    finder_wrap_enabled,
    format_size,
)

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


def is_saved_file(filepath):
    return bool(filepath) and os.path.isfile(filepath)


def is_text_document(ed):
    return ed.get_prop(PROP_KIND) == 'text'


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


def editor_lines(ed):
    return [ed.get_text_line(i) for i in range(ed.get_line_count())]


def editor_handle(ed):
    return ed.get_prop(PROP_HANDLE_SELF)


def highlight_is_present(ed):
    marks = ed.attr(MARKERS_GET_DICT) or []
    for mark in marks:
        if isinstance(mark, dict) and mark.get('tag') == NONASCII_MARK_TAG:
            return True
    return False


def highlight_nonascii(ed):
    ed.attr(MARKERS_DELETE_BY_TAG, NONASCII_MARK_TAG)
    xs, ys, lens = collect_nonascii_positions(editor_lines(ed))
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


def get_finder_wrap():
    try:
        prop = app_proc(PROC_GET_FINDER_PROP, '')
    except Exception:
        return False
    return finder_wrap_enabled(prop)


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


def _log_error(where):
    # print() goes to CudaText Console; traceback.print_exc() goes to stderr
    # and is often invisible there.
    print('cuda_tabmenu error in %s:\n%s' % (where, traceback.format_exc()))
    sys.stdout.flush()
    msg_status(_('Tab Menu error; see Console'))


print('cuda_tabmenu module imported, version %s' % __version__)
sys.stdout.flush()


class Command:

    def __init__(self):
        self._tab_ed = None
        self._highlighted = set()
        self._tab_menu_handle = None
        print('Tab Menu Command() created, version %s' % __version__)
        sys.stdout.flush()

    def on_start(self, ed_self):
        print('Tab Menu %s loaded' % __version__)
        sys.stdout.flush()
        msg_status('Tab Menu %s loaded' % __version__)

    def _tab_root(self):
        # String id 'tab' calls InitPopupTab on every menu_proc access and
        # rebuilds the stock popup, wiping plugin items. Resolve the numeric
        # handle once, then add only to that handle.
        if self._tab_menu_handle not in (None, '', 0, '0'):
            return self._tab_menu_handle
        prop = menu_proc('tab', MENU_GET_PROP)
        handle = prop.get('id') if isinstance(prop, dict) else None
        if handle not in (None, '', 0, '0'):
            self._tab_menu_handle = handle
            return handle
        return 'tab'

    def _current_ed(self, prefer_tab=False):
        if prefer_tab and self._tab_ed is not None:
            return self._tab_ed
        try:
            if prefer_tab:
                clicked = Editor(1)
                if clicked is not None:
                    return clicked
        except Exception:
            pass
        return ed

    def on_tab_menu(self, ed_self):
        try:
            self._tab_ed = ed_self
            tab_id = self._tab_root()
            can_open_path = is_saved_file(ed_self.get_filename())
            self._set_menu_item(tab_id, CAP_INFO, self.menu_info, True)
            self._set_menu_item(tab_id, CAP_OPEN_PATH, self.menu_open_path, can_open_path)
            self._set_nonascii_submenu(tab_id, 'menu', is_text_document(ed_self))
        except Exception:
            _log_error('on_tab_menu')

    def on_init_plugins_menu(self, ed_self):
        try:
            self._install_search_menu()
        except Exception:
            _log_error('on_init_plugins_menu')

    def on_change_slow(self, ed_self):
        try:
            if not self._is_highlight_active(ed_self):
                return
            if not is_text_document(ed_self):
                self._clear_highlight(ed_self)
                return
            highlight_nonascii(ed_self)
        except Exception:
            _log_error('on_change_slow')

    def _mark_highlighted(self, ed, active):
        handle = editor_handle(ed)
        if active:
            self._highlighted.add(handle)
        else:
            self._highlighted.discard(handle)

    def _is_highlight_active(self, ed):
        handle = editor_handle(ed)
        if handle in self._highlighted:
            return True
        if highlight_is_present(ed):
            self._highlighted.add(handle)
            return True
        return False

    def _clear_highlight(self, ed):
        unhighlight_nonascii(ed)
        self._mark_highlighted(ed, False)

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
        for item in menu_proc(menu_id, MENU_ENUM) or []:
            if item.get('cap') == caption:
                menu_proc(item['id'], MENU_REMOVE)
                return True
        return False

    def _add_menu_item(self, parent_id, caption, command, enabled=True):
        item_id = menu_proc(parent_id, MENU_ADD, caption=caption, command=command)
        if not enabled and item_id:
            menu_proc(item_id, MENU_SET_ENABLED, command=False)
        return item_id

    def _set_menu_item(self, parent_id, caption, command, enabled):
        self._remove_menu_item(parent_id, caption)
        self._add_menu_item(parent_id, caption, command, enabled)

    def _add_nonascii_submenu(self, parent_id, cmd_prefix, enabled):
        sub_id = menu_proc(parent_id, MENU_ADD, caption=CAP_NONASCII)
        if not enabled:
            menu_proc(sub_id, MENU_SET_ENABLED, command=False)
        self._fill_nonascii_submenu(sub_id, cmd_prefix, enabled)

    def _set_nonascii_submenu(self, parent_id, cmd_prefix, enabled):
        self._remove_menu_item(parent_id, CAP_NONASCII)
        self._add_nonascii_submenu(parent_id, cmd_prefix, enabled)

    def _nonascii_commands(self, cmd_prefix):
        if cmd_prefix == 'menu':
            return [
                (CAP_HIGHLIGHT_NONASCII, self.menu_highlight_nonascii),
                (CAP_UNHIGHLIGHT_NONASCII, self.menu_unhighlight_nonascii),
                ('-', None),
                (CAP_NEXT_NONASCII, self.menu_next_nonascii),
                (CAP_PREV_NONASCII, self.menu_prev_nonascii),
                ('-', None),
                (CAP_TRANSLITERATE_ASCII, self.menu_transliterate_ascii),
            ]
        return [
            (CAP_HIGHLIGHT_NONASCII, self.search_highlight_nonascii),
            (CAP_UNHIGHLIGHT_NONASCII, self.search_unhighlight_nonascii),
            ('-', None),
            (CAP_NEXT_NONASCII, self.search_next_nonascii),
            (CAP_PREV_NONASCII, self.search_prev_nonascii),
            ('-', None),
            (CAP_TRANSLITERATE_ASCII, self.search_transliterate_ascii),
        ]

    def _fill_nonascii_submenu(self, parent_id, cmd_prefix, enabled=True):
        for caption, command in self._nonascii_commands(cmd_prefix):
            if caption == '-':
                menu_proc(parent_id, MENU_ADD, caption='-')
                continue
            self._add_menu_item(parent_id, caption, command, enabled)

    def menu_info(self, info=''):
        try:
            self._show_info_dialog(self._current_ed(prefer_tab=True))
        except Exception:
            _log_error('menu_info')

    def search_info(self, info=''):
        try:
            msg_status(_('Tab Menu: Info'))
            self._show_info_dialog(self._current_ed())
        except Exception:
            _log_error('search_info')

    def menu_open_path(self, info=''):
        try:
            ed_tab = self._current_ed(prefer_tab=True)
            filepath = ed_tab.get_filename()
            if not is_saved_file(filepath):
                return
            open_folder(os.path.dirname(os.path.abspath(filepath)))
        except Exception:
            _log_error('menu_open_path')

    def _ed_text(self, ed):
        if ed is None or not is_text_document(ed):
            return None
        return ed

    def _do_highlight_nonascii(self, ed):
        try:
            ed = self._ed_text(ed)
            if ed is None:
                msg_status(_('Not a text document'))
                return
            count = highlight_nonascii(ed)
            self._mark_highlighted(ed, True)
            msg_status(_('Highlighted {} non-ASCII character(s)').format(count))
        except Exception:
            _log_error('highlight_nonascii')

    def _do_unhighlight_nonascii(self, ed):
        try:
            ed = self._ed_text(ed)
            if ed is None:
                msg_status(_('Not a text document'))
                return
            self._clear_highlight(ed)
            msg_status(_('Non-ASCII highlights removed'))
        except Exception:
            _log_error('unhighlight_nonascii')

    def _goto_found_nonascii(self, ed, result):
        if result is None:
            msg_status(_('No more non-ASCII characters'))
            return
        col, row, wrapped = result
        goto_nonascii(ed, (col, row))
        if wrapped:
            msg_status(_('Wrapped search'))

    def _do_next_nonascii(self, ed):
        try:
            ed = self._ed_text(ed)
            if ed is None:
                msg_status(_('Not a text document'))
                return
            x, y, x1, y1 = ed.get_carets()[0]
            self._goto_found_nonascii(
                ed,
                find_next_nonascii(editor_lines(ed), x, y, wrap=get_finder_wrap()),
            )
        except Exception:
            _log_error('next_nonascii')

    def _do_prev_nonascii(self, ed):
        try:
            ed = self._ed_text(ed)
            if ed is None:
                msg_status(_('Not a text document'))
                return
            x, y, x1, y1 = ed.get_carets()[0]
            self._goto_found_nonascii(
                ed,
                find_prev_nonascii(editor_lines(ed), x, y, wrap=get_finder_wrap()),
            )
        except Exception:
            _log_error('prev_nonascii')

    def menu_highlight_nonascii(self, info=''):
        self._do_highlight_nonascii(self._current_ed(prefer_tab=True))

    def menu_unhighlight_nonascii(self, info=''):
        self._do_unhighlight_nonascii(self._current_ed(prefer_tab=True))

    def menu_next_nonascii(self, info=''):
        self._do_next_nonascii(self._current_ed(prefer_tab=True))

    def menu_prev_nonascii(self, info=''):
        self._do_prev_nonascii(self._current_ed(prefer_tab=True))

    def search_highlight_nonascii(self, info=''):
        self._do_highlight_nonascii(self._current_ed())

    def search_unhighlight_nonascii(self, info=''):
        self._do_unhighlight_nonascii(self._current_ed())

    def search_next_nonascii(self, info=''):
        self._do_next_nonascii(self._current_ed())

    def search_prev_nonascii(self, info=''):
        self._do_prev_nonascii(self._current_ed())

    def _do_transliterate_ascii(self, ed):
        try:
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

            keep_highlight = self._is_highlight_active(ed)
            ed.set_text_all(new_text)
            if keep_highlight:
                highlight_nonascii(ed)
                self._mark_highlighted(ed, True)
            msg_status(_('Transliterated to ASCII'))
        except Exception:
            _log_error('transliterate_ascii')

    def menu_transliterate_ascii(self, info=''):
        self._do_transliterate_ascii(self._current_ed(prefer_tab=True))

    def search_transliterate_ascii(self, info=''):
        self._do_transliterate_ascii(self._current_ed())

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

        text = None
        if saved:
            lines.append(_('Size on disk: {}').format(format_size(os.path.getsize(filepath))))

        if modified or not saved:
            text = ed.get_text_all()
            lines.append(_('Size in memory: {}').format(format_size(len(text.encode('utf-8')))))

        if is_text_document(ed):
            line_count = ed.get_line_count()
            lines.append(_('Line count: {}').format(line_count))
            if text is None:
                text = ed.get_text_all()
            lines.append(_('Word count: {}').format(count_words(text)))

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
