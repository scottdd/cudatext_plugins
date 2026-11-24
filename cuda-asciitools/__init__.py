import sys
import traceback

__version__ = '0.2.0'

from cudatext import *
from cudax_lib import get_translation

from .anyascii import anyascii as transliterate_to_ascii
from .logic import (
    caption_with_hotkey,
    collect_nonascii_in_spans,
    collect_nonascii_positions,
    find_next_nonascii,
    find_prev_nonascii,
    finder_wrap_enabled,
    format_nonascii_report,
    lookup_command_hotkey,
    normalize_punctuation,
    selections_from_carets,
    strip_nonascii,
    tab_handle_from_prop,
    usable_menu_handle,
)

_ = get_translation(__file__)

CAP_MENU = _('ASCII Tools')
CAP_HIGHLIGHT = _('Highlight Non-ASCII')
CAP_UNHIGHLIGHT = _('Un-highlight Non-ASCII')
CAP_NEXT = _('Next Non-ASCII Character')
CAP_PREV = _('Previous Non-ASCII Character')
CAP_TRANSLITERATE = _('Transliterate to ASCII')
CAP_LIST = _('List Non-ASCII Characters')
CAP_STRIP = _('Strip Non-ASCII Characters')
CAP_NORMALIZE = _('Normalize Punctuation && Spaces to ASCII')
CAP_REPORT = _('Non-ASCII Characters')

NONASCII_MARK_TAG = 88021
NONASCII_HIGHLIGHT_STYLE = dict(
    color_bg='#FFE8A0',
    border_down=4,
)
SEARCH_MENU_TAG = 'cuda_asciitools_search'
TAB_TAG_PREFIX = 'cuda_asciitools_tab_'
COMMAND_MODULE = 'cuda_asciitools'


def is_text_document(editor):
    return editor.get_prop(PROP_KIND) == 'text'


def editor_lines(editor):
    return [editor.get_text_line(i) for i in range(editor.get_line_count())]


def editor_handle(editor):
    return editor.get_prop(PROP_HANDLE_SELF)


def highlight_is_present(editor):
    marks = editor.attr(MARKERS_GET_DICT) or []
    for mark in marks:
        if isinstance(mark, dict) and mark.get('tag') == NONASCII_MARK_TAG:
            return True
    return False


def highlight_nonascii(editor):
    editor.attr(MARKERS_DELETE_BY_TAG, NONASCII_MARK_TAG)
    xs, ys, lens = collect_nonascii_positions(editor_lines(editor))
    if xs:
        editor.attr(MARKERS_ADD_MANY, NONASCII_MARK_TAG, xs, ys, lens, **NONASCII_HIGHLIGHT_STYLE)
    return len(xs)


def unhighlight_nonascii(editor):
    editor.attr(MARKERS_DELETE_BY_TAG, NONASCII_MARK_TAG)


def goto_nonascii(editor, pos):
    if pos is None:
        return False
    col, row = pos
    editor.set_caret(col, row, col + 1, row)
    editor.focus()
    return True


def get_finder_wrap():
    try:
        prop = app_proc(PROC_GET_FINDER_PROP, '')
    except Exception:
        return False
    return finder_wrap_enabled(prop)


def _log_error(where):
    # print() goes to the CudaText Console. traceback.print_exc() goes to
    # stderr, which the Console does not show.
    print('cuda_asciitools error in %s:\n%s' % (where, traceback.format_exc()))
    sys.stdout.flush()
    msg_status(_('ASCII Tools error; see Console'))


print('cuda_asciitools module imported, version %s' % __version__)
sys.stdout.flush()


class Command:

    def __init__(self):
        self._highlighted = set()
        self._dialog_text = ''
        self._dialog_action = None
        self._tab_ed = None
        self._tab_menu_handle = None
        self._search_hotkey_sig = None

    def on_start(self, ed_self):
        print('ASCII Tools %s loaded' % __version__)
        sys.stdout.flush()
        # Resolve the string id now, before any plugin adds popup items.
        # Touching it again calls InitPopupTab. Current CudaText builds that
        # popup only once; older builds rebuilt it and dropped plugin items.
        try:
            self._tab_root()
        except Exception:
            _log_error('on_start')

    def on_init_plugins_menu(self, ed_self):
        try:
            self._install_search_menu()
        except Exception:
            _log_error('on_init_plugins_menu')

    def on_focus(self, ed_self):
        # F9 writes keys.json and refreshes the Plugins menu without an
        # on_state. Closing that dialog returns focus here, so the Search
        # submenu can pick up the new PROC_GET_HOTKEY values. APPSTATE_CONFIG_REREAD
        # is user.json, not keys.json; on_state still refreshes when it fires.
        try:
            sig = self._hotkey_signature()
            if sig == self._search_hotkey_sig:
                return
            self._install_search_menu()
        except Exception:
            _log_error('on_focus')

    def on_state(self, ed_self, state):
        try:
            if state != APPSTATE_CONFIG_REREAD:
                return
            self._search_hotkey_sig = None
            self._install_search_menu()
        except Exception:
            _log_error('on_state')

    def on_tab_menu(self, ed_self):
        try:
            self._tab_ed = ed_self
            tab_id = self._tab_root()
            self._clear_our_tab_items(tab_id)
            menu_proc(tab_id, MENU_ADD, caption='-', tag=TAB_TAG_PREFIX + 'sep')
            sub_id = menu_proc(
                tab_id,
                MENU_ADD,
                caption=CAP_MENU,
                tag=TAB_TAG_PREFIX + 'menu',
            )
            self._fill_menu(sub_id, for_tab=True)
            if sub_id and not is_text_document(ed_self):
                menu_proc(sub_id, MENU_SET_ENABLED, command=False)
        except Exception:
            _log_error('on_tab_menu')

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

    def _mark_highlighted(self, editor, active):
        handle = editor_handle(editor)
        if active:
            self._highlighted.add(handle)
        else:
            self._highlighted.discard(handle)

    def _is_highlight_active(self, editor):
        handle = editor_handle(editor)
        if handle in self._highlighted:
            return True
        if highlight_is_present(editor):
            self._highlighted.add(handle)
            return True
        return False

    def _clear_highlight(self, editor):
        unhighlight_nonascii(editor)
        self._mark_highlighted(editor, False)

    def _rehighlight(self, editor):
        if not self._is_highlight_active(editor):
            return
        highlight_nonascii(editor)
        self._mark_highlighted(editor, True)

    def _ed_text(self, editor):
        if editor is None:
            editor = ed
        if editor is None or not is_text_document(editor):
            return None
        return editor

    def _read_hotkey(self, command_id):
        return app_proc(PROC_GET_HOTKEY, command_id)

    def _lookup_hotkey(self, method_name):
        return lookup_command_hotkey(self._read_hotkey, COMMAND_MODULE + ',' + method_name)

    def _hotkey_signature(self):
        parts = []
        for spec in self._command_specs():
            if spec[0] == '-':
                continue
            parts.append(self._lookup_hotkey(spec[2]))
        return tuple(parts)

    def _tab_root(self):
        # One string-id access, during on_start. on_tab_menu uses the number.
        cached = usable_menu_handle(self._tab_menu_handle)
        if cached is not None:
            return cached
        handle = tab_handle_from_prop(menu_proc('tab', MENU_GET_PROP))
        if handle is not None:
            self._tab_menu_handle = handle
            return handle
        return 'tab'

    def _clear_our_tab_items(self, menu_id):
        items = menu_proc(menu_id, MENU_ENUM) or []
        ids = []
        for item in items:
            tag = item.get('tag')
            if isinstance(tag, str) and tag.startswith(TAB_TAG_PREFIX):
                ids.append(item['id'])
        for item_id in ids:
            menu_proc(item_id, MENU_REMOVE)

    def _install_search_menu(self):
        self._search_hotkey_sig = self._hotkey_signature()
        items = menu_proc('top-sr', MENU_ENUM) or []
        existing = [item for item in items if item.get('tag') == SEARCH_MENU_TAG]
        if existing:
            parent_id = existing[0]['id']
            menu_proc(parent_id, MENU_CLEAR)
            self._fill_menu(parent_id, for_tab=False)
            return
        menu_proc('top-sr', MENU_ADD, caption='-', tag=SEARCH_MENU_TAG + '_sep')
        parent_id = menu_proc('top-sr', MENU_ADD, caption=CAP_MENU, tag=SEARCH_MENU_TAG)
        self._fill_menu(parent_id, for_tab=False)

    def _command_specs(self):
        # (caption, active-editor callback, install.inf method, tab callback)
        return [
            (CAP_HIGHLIGHT, self.menu_highlight_nonascii, 'menu_highlight_nonascii', self.tab_highlight_nonascii),
            (CAP_UNHIGHLIGHT, self.menu_unhighlight_nonascii, 'menu_unhighlight_nonascii', self.tab_unhighlight_nonascii),
            ('-', None, None, None),
            (CAP_NEXT, self.menu_next_nonascii, 'menu_next_nonascii', self.tab_next_nonascii),
            (CAP_PREV, self.menu_prev_nonascii, 'menu_prev_nonascii', self.tab_prev_nonascii),
            ('-', None, None, None),
            (CAP_LIST, self.menu_list_nonascii, 'menu_list_nonascii', self.tab_list_nonascii),
            ('-', None, None, None),
            (CAP_TRANSLITERATE, self.menu_transliterate_ascii, 'menu_transliterate_ascii', self.tab_transliterate_ascii),
            (CAP_STRIP, self.menu_strip_nonascii, 'menu_strip_nonascii', self.tab_strip_nonascii),
            (CAP_NORMALIZE, self.menu_normalize_punctuation, 'menu_normalize_punctuation', self.tab_normalize_punctuation),
        ]

    def _fill_menu(self, parent_id, for_tab):
        for caption, active_command, method_name, tab_command in self._command_specs():
            if caption == '-':
                menu_proc(parent_id, MENU_ADD, caption='-')
                continue
            shown = caption_with_hotkey(caption, self._lookup_hotkey(method_name))
            command = tab_command if for_tab else active_command
            # hotkey= is intentionally omitted. See logic.caption_with_hotkey.
            menu_proc(parent_id, MENU_ADD, caption=shown, command=command)

    def _do_highlight(self, editor):
        try:
            editor = self._ed_text(editor)
            if editor is None:
                msg_status(_('Not a text document'))
                return
            count = highlight_nonascii(editor)
            self._mark_highlighted(editor, True)
            msg_status(_('Highlighted {} non-ASCII character(s)').format(count))
        except Exception:
            _log_error('highlight_nonascii')

    def _do_unhighlight(self, editor):
        try:
            editor = self._ed_text(editor)
            if editor is None:
                msg_status(_('Not a text document'))
                return
            self._clear_highlight(editor)
            msg_status(_('Non-ASCII highlights removed'))
        except Exception:
            _log_error('unhighlight_nonascii')

    def _goto_found(self, editor, result):
        if result is None:
            msg_status(_('No more non-ASCII characters'))
            return
        col, row, wrapped = result
        goto_nonascii(editor, (col, row))
        if wrapped:
            msg_status(_('Wrapped search'))

    def _caret(self, editor):
        carets = editor.get_carets() or []
        if not carets:
            return 0, 0
        return carets[0][0], carets[0][1]

    def _do_next(self, editor):
        try:
            editor = self._ed_text(editor)
            if editor is None:
                msg_status(_('Not a text document'))
                return
            x, y = self._caret(editor)
            self._goto_found(
                editor,
                find_next_nonascii(editor_lines(editor), x, y, wrap=get_finder_wrap()),
            )
        except Exception:
            _log_error('next_nonascii')

    def _do_prev(self, editor):
        try:
            editor = self._ed_text(editor)
            if editor is None:
                msg_status(_('Not a text document'))
                return
            x, y = self._caret(editor)
            self._goto_found(
                editor,
                find_prev_nonascii(editor_lines(editor), x, y, wrap=get_finder_wrap()),
            )
        except Exception:
            _log_error('prev_nonascii')

    def _apply_transform(self, editor, transform, confirm_message, unchanged_message, done_message):
        try:
            editor = self._ed_text(editor)
            if editor is None:
                msg_status(_('Not a text document'))
                return
            if editor.get_prop(PROP_RO):
                msg_status(_('Document is read-only'))
                return
            spans = list(reversed(selections_from_carets(editor.get_carets())))
            if not spans:
                if msg_box(confirm_message, MB_OKCANCEL + MB_ICONQUESTION) != ID_OK:
                    return
                text = editor.get_text_all()
                new_text = transform(text or '')
                if new_text == (text or ''):
                    msg_status(unchanged_message)
                    return
                editor.replace(0, 0, 0, editor.get_line_count(), new_text)
                self._rehighlight(editor)
                msg_status(done_message)
                return
            changed = False
            for x1, y1, x2, y2 in spans:
                text = editor.get_text_substr(x1, y1, x2, y2) or ''
                new_text = transform(text)
                if new_text != text:
                    editor.replace(x1, y1, x2, y2, new_text)
                    changed = True
            if not changed:
                msg_status(unchanged_message)
                return
            self._rehighlight(editor)
            msg_status(done_message)
        except Exception:
            _log_error('transform')

    def _do_transliterate(self, editor):
        self._apply_transform(
            editor,
            transliterate_to_ascii,
            _('Transliterate all non-ASCII characters to ASCII in this document?'),
            _('No non-ASCII characters found'),
            _('Transliterated to ASCII'),
        )

    def _do_strip(self, editor):
        self._apply_transform(
            editor,
            strip_nonascii,
            _('Remove all non-ASCII characters from this document?'),
            _('No non-ASCII characters found'),
            _('Removed non-ASCII characters'),
        )

    def _do_normalize(self, editor):
        self._apply_transform(
            editor,
            normalize_punctuation,
            _('Normalize punctuation and spaces to ASCII in this document? Accented letters are kept.'),
            _('No punctuation or spaces to normalize'),
            _('Normalized punctuation and spaces'),
        )

    def _do_list(self, editor):
        try:
            editor = self._ed_text(editor)
            if editor is None:
                msg_status(_('Not a text document'))
                return
            lines = editor_lines(editor)
            spans = selections_from_carets(editor.get_carets())
            if spans:
                entries = collect_nonascii_in_spans(lines, spans)
                scope = 'selection'
            else:
                entries = collect_nonascii_in_spans(lines, None)
                scope = 'whole document'
            if not entries:
                msg_status(_('No non-ASCII characters found'))
                return
            report = format_nonascii_report(entries, scope=scope)
            action = self._show_text_dialog(CAP_REPORT, report)
            if action == 'tab':
                self._open_scratch(report)
        except Exception:
            _log_error('list_nonascii')

    def _show_text_dialog(self, caption, text):
        self._dialog_text = text
        self._dialog_action = None
        w = 640
        h = 420
        dlg = dlg_proc(0, DLG_CREATE)
        dlg_proc(dlg, DLG_PROP_SET, prop={
            'cap': caption,
            'w': w,
            'h': h,
            'w_min': 420,
            'h_min': 220,
            'border': DBORDER_SIZE,
        })

        close_btn = dlg_proc(dlg, DLG_CTL_ADD, prop='button')
        dlg_proc(dlg, DLG_CTL_PROP_SET, index=close_btn, prop={
            'name': 'btn_close',
            'cap': _('&Close'),
            'a_l': None,
            'a_t': None,
            'a_r': ('', ']'),
            'a_b': ('', ']'),
            'sp_a': 6,
            'x': w - 100,
            'y': h - 6 - 25,
            'w': 94,
            'on_change': self._dialog_close,
            'ex0': True,
        })

        tab_btn = dlg_proc(dlg, DLG_CTL_ADD, prop='button')
        dlg_proc(dlg, DLG_CTL_PROP_SET, index=tab_btn, prop={
            'name': 'btn_tab',
            'cap': _('Open in &Tab'),
            'a_l': None,
            'a_t': None,
            'a_r': ('btn_close', '['),
            'a_b': ('', ']'),
            'sp_r': 6,
            'sp_b': 6,
            'x': w - 220,
            'y': h - 6 - 25,
            'w': 114,
            'on_change': self._dialog_open_tab,
        })

        copy_btn = dlg_proc(dlg, DLG_CTL_ADD, prop='button')
        dlg_proc(dlg, DLG_CTL_PROP_SET, index=copy_btn, prop={
            'name': 'btn_copy',
            'cap': _('&Copy'),
            'a_l': None,
            'a_t': None,
            'a_r': ('btn_tab', '['),
            'a_b': ('', ']'),
            'sp_r': 6,
            'sp_b': 6,
            'x': w - 320,
            'y': h - 6 - 25,
            'w': 94,
            'on_change': self._dialog_copy,
        })

        memo = dlg_proc(dlg, DLG_CTL_ADD, prop='memo')
        dlg_proc(dlg, DLG_CTL_PROP_SET, index=memo, prop={
            'name': 'memo_text',
            'val': text,
            'a_r': ('', ']'),
            'a_b': ('btn_close', '['),
            'sp_a': 6,
            'x': 6,
            'y': 6,
            'w': w - 12,
            'h': h - 6 - 25 - 12,
            'ex0': True,
            'ex1': True,
            'ro': True,
        })

        dlg_proc(dlg, DLG_CTL_FOCUS, name='btn_close')
        dlg_proc(dlg, DLG_SCALE)
        dlg_proc(dlg, DLG_SHOW_MODAL)
        dlg_proc(dlg, DLG_FREE)
        return self._dialog_action

    def _dialog_close(self, id_dlg, id_ctl, data='', info=''):
        dlg_proc(id_dlg, DLG_HIDE)

    def _dialog_copy(self, id_dlg, id_ctl, data='', info=''):
        app_proc(PROC_SET_CLIP, self._dialog_text)
        msg_status(_('Copied'))

    def _dialog_open_tab(self, id_dlg, id_ctl, data='', info=''):
        self._dialog_action = 'tab'
        dlg_proc(id_dlg, DLG_HIDE)

    def _looks_empty(self, editor):
        if editor.get_filename():
            return False
        text = editor.get_text_all() or ''
        return text.strip('\n\r') == ''

    def _open_scratch(self, text):
        before = editor_handle(ed)
        if not file_open(''):
            msg_status(_('Could not open a new tab'))
            return
        current = ed
        if editor_handle(current) == before and not self._looks_empty(current):
            msg_status(_('Could not open a new tab'))
            return
        current.set_text_all(text)
        current.set_prop(PROP_TAB_TITLE, CAP_REPORT)
        try:
            current.set_prop(PROP_MODIFIED, False)
        except Exception:
            pass
        msg_status(_('Listed non-ASCII characters in a new tab'))

    def menu_highlight_nonascii(self, info=''):
        self._do_highlight(ed)

    def menu_unhighlight_nonascii(self, info=''):
        self._do_unhighlight(ed)

    def menu_next_nonascii(self, info=''):
        self._do_next(ed)

    def menu_prev_nonascii(self, info=''):
        self._do_prev(ed)

    def menu_transliterate_ascii(self, info=''):
        self._do_transliterate(ed)

    def menu_list_nonascii(self, info=''):
        self._do_list(ed)

    def menu_strip_nonascii(self, info=''):
        self._do_strip(ed)

    def menu_normalize_punctuation(self, info=''):
        self._do_normalize(ed)

    def tab_highlight_nonascii(self, info=''):
        self._do_highlight(self._tab_ed)

    def tab_unhighlight_nonascii(self, info=''):
        self._do_unhighlight(self._tab_ed)

    def tab_next_nonascii(self, info=''):
        self._do_next(self._tab_ed)

    def tab_prev_nonascii(self, info=''):
        self._do_prev(self._tab_ed)

    def tab_transliterate_ascii(self, info=''):
        self._do_transliterate(self._tab_ed)

    def tab_list_nonascii(self, info=''):
        self._do_list(self._tab_ed)

    def tab_strip_nonascii(self, info=''):
        self._do_strip(self._tab_ed)

    def tab_normalize_punctuation(self, info=''):
        self._do_normalize(self._tab_ed)
