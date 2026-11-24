import os
import shutil
import subprocess
import sys
import traceback

__version__ = '0.7.2'

from cudatext import *
from cudatext_cmd import cmd_FileClose, cmd_FileExportHtml, cmd_FileReopen
from cudax_lib import get_translation

from .logic import (
    FileOpError,
    available_attempts,
    build_file_info_dialog,
    button_ex_label,
    caption_with_hotkey,
    clean_duplicate_basename,
    file_info_key_action,
    count_characters,
    count_words,
    encode_document,
    first_path,
    format_line_endings,
    format_size,
    format_status,
    format_timestamp,
    lookup_command_hotkey,
    open_folder_attempts,
    platform_from_suffix,
    prepare_destination,
    reveal_attempts,
    safe_copy_file,
    safe_delete_file,
    safe_write_bytes,
    suggest_duplicate_name,
    tab_handle_from_prop,
    terminal_attempts,
    usable_menu_handle,
)

_ = get_translation(__file__)

CAP_FILE_INFO = _('File &Info...')
CAP_REVEAL = _('&Reveal in File Manager')
CAP_OPEN_FOLDER = _('Open &Folder')
CAP_TERMINAL = _('Open &Terminal Here')
CAP_RELOAD = _('Reo&pen / Reload from Disk')
CAP_SAVE_COPY = _('&Save a Copy As...')
CAP_DUPLICATE = _('D&uplicate File')
CAP_DELETE = _('Close and &Delete File...')
CAP_EXPORT = _('&Export to HTML...')
CAP_DIALOG = _('File Info')
CAP_NONE = _('(none)')
CAP_UNSAVED = _('(unsaved)')

TAG_PREFIX = 'cuda_tabmenu_item_'
COMMAND_MODULE = 'cuda_tabmenu'

OS_PLATFORM = platform_from_suffix(app_proc(PROC_GET_OS_SUFFIX, ''))


def is_saved_file(filepath):
    return bool(filepath) and os.path.isfile(filepath)


def is_text_document(editor):
    return editor.get_prop(PROP_KIND) == 'text'


def _log_error(where):
    # print() goes to the CudaText Console. traceback.print_exc() goes to
    # stderr, which the Console does not show.
    print('cuda_tabmenu error in %s:\n%s' % (where, traceback.format_exc()))
    sys.stdout.flush()
    msg_status(_('Tab Menu error; see Console'))


def _program_exists(name):
    return shutil.which(name) is not None


def _ui_theme_dict():
    """Active UI theme, or None when the API is missing or returns something else."""
    try:
        theme = app_proc(PROC_THEME_UI_DICT_GET, '')
    except Exception:
        return None
    if isinstance(theme, dict):
        return theme
    return None


print('cuda_tabmenu module imported, version %s' % __version__)
sys.stdout.flush()


class Command:

    def __init__(self):
        self._tab_ed = None
        self._tab_menu_handle = None
        self._dialog_text = ''

    def on_start(self, ed_self):
        print('Tab Menu %s loaded' % __version__)
        sys.stdout.flush()
        # Resolve the string id before on_tab_menu. If another plugin also
        # resolves it on the first right-click, InitPopupTab on an older
        # CudaText rebuilds the popup and drops whoever added items first.
        # Current builds create PopupTab only while it is nil; caching still
        # keeps this plugin off the string id once items exist.
        try:
            self._tab_root()
        except Exception:
            _log_error('on_start')

    def _tab_root(self):
        cached = usable_menu_handle(self._tab_menu_handle)
        if cached is not None:
            return cached
        handle = tab_handle_from_prop(menu_proc('tab', MENU_GET_PROP))
        if handle is not None:
            self._tab_menu_handle = handle
            return handle
        return 'tab'

    def _read_hotkey(self, command_id):
        return app_proc(PROC_GET_HOTKEY, command_id)

    def _hotkey_caption(self, caption, method_name):
        raw = lookup_command_hotkey(self._read_hotkey, COMMAND_MODULE + ',' + method_name)
        return caption_with_hotkey(caption, raw)

    def _current_ed(self, prefer_tab=False):
        if prefer_tab and self._tab_ed is not None:
            return self._tab_ed
        return ed

    def _clear_our_items(self, menu_id):
        items = menu_proc(menu_id, MENU_ENUM) or []
        ids = []
        for item in items:
            tag = item.get('tag')
            if isinstance(tag, str) and tag.startswith(TAG_PREFIX):
                ids.append(item['id'])
        for item_id in ids:
            menu_proc(item_id, MENU_REMOVE)

    def _add_item(self, parent_id, key, caption, command, enabled, method_name):
        # hotkey= is omitted. The Plugins item already owns ShortCut for method_name.
        item_id = menu_proc(
            parent_id,
            MENU_ADD,
            caption=self._hotkey_caption(caption, method_name),
            command=command,
            tag=TAG_PREFIX + key,
        )
        if item_id and not enabled:
            menu_proc(item_id, MENU_SET_ENABLED, command=False)
        return item_id

    def on_tab_menu(self, ed_self):
        try:
            self._tab_ed = ed_self
            tab_id = self._tab_root()
            saved = is_saved_file(ed_self.get_filename())
            text_doc = is_text_document(ed_self)
            self._clear_our_items(tab_id)
            menu_proc(tab_id, MENU_ADD, caption='-', tag=TAG_PREFIX + 'sep')
            self._add_item(tab_id, 'info', CAP_FILE_INFO, self.menu_file_info, True, 'cmd_file_info')
            self._add_item(tab_id, 'reveal', CAP_REVEAL, self.menu_reveal, saved, 'cmd_reveal')
            self._add_item(tab_id, 'folder', CAP_OPEN_FOLDER, self.menu_open_folder, saved, 'cmd_open_folder')
            self._add_item(tab_id, 'terminal', CAP_TERMINAL, self.menu_terminal, saved, 'cmd_open_terminal')
            self._add_item(tab_id, 'reload', CAP_RELOAD, self.menu_reload, saved, 'cmd_reload')
            self._add_item(tab_id, 'savecopy', CAP_SAVE_COPY, self.menu_save_copy, True, 'cmd_save_copy')
            self._add_item(tab_id, 'duplicate', CAP_DUPLICATE, self.menu_duplicate, saved, 'cmd_duplicate')
            self._add_item(tab_id, 'delete', CAP_DELETE, self.menu_close_delete, saved, 'cmd_close_delete')
            self._add_item(tab_id, 'html', CAP_EXPORT, self.menu_export_html, text_doc, 'cmd_export_html')
        except Exception:
            _log_error('on_tab_menu')

    def _require_saved(self, editor):
        path = editor.get_filename()
        if not is_saved_file(path):
            msg_status(_('Unsaved tab has no file on disk'))
            return None
        return os.path.abspath(path)

    def _run_popen(self, attempt):
        kwargs = {}
        if attempt.get('cwd'):
            kwargs['cwd'] = attempt['cwd']
        subprocess.Popen(attempt['argv'], **kwargs)

    def _run_first(self, attempts, failure_message):
        chosen = available_attempts(attempts, _program_exists)
        if not chosen:
            msg_status(failure_message)
            return False
        attempt = chosen[0]
        try:
            self._run_popen(attempt)
        except Exception as ex:
            msg_status(failure_message + ': ' + str(ex))
            return False
        return True

    def _run_until_ok(self, attempts, failure_message):
        chosen = available_attempts(attempts, _program_exists)
        if not chosen:
            msg_status(failure_message)
            return False
        errors = []
        for attempt in chosen:
            try:
                if attempt.get('wait'):
                    proc = subprocess.run(
                        attempt['argv'],
                        cwd=attempt.get('cwd') or None,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=8,
                    )
                    if proc.returncode == 0:
                        return True
                    err = (proc.stderr or b'').decode('utf-8', 'replace').strip()
                    if err:
                        errors.append(err.splitlines()[-1][:200])
                    continue
                self._run_popen(attempt)
                return True
            except Exception as ex:
                errors.append(str(ex))
        detail = errors[-1] if errors else failure_message
        msg_status(detail)
        return False

    def _reveal(self, editor):
        try:
            path = self._require_saved(editor)
            if not path:
                return
            attempts = reveal_attempts(OS_PLATFORM, path)
            if not attempts:
                msg_status(_('Reveal in File Manager is not implemented for this OS'))
                return
            self._run_until_ok(attempts, _('Could not reveal the file'))
        except Exception:
            _log_error('reveal')

    def _open_folder(self, editor):
        try:
            path = self._require_saved(editor)
            if not path:
                return
            folder = os.path.dirname(path)
            if not os.path.isdir(folder):
                msg_status(_('Folder not found: {}').format(folder))
                return
            attempts = open_folder_attempts(OS_PLATFORM, folder)
            if not attempts:
                msg_status(_('Open Folder is not implemented for this OS'))
                return
            self._run_first(attempts, _('Could not open the folder'))
        except Exception:
            _log_error('open_folder')

    def _open_terminal(self, editor):
        try:
            path = self._require_saved(editor)
            if not path:
                return
            folder = os.path.dirname(path)
            if not os.path.isdir(folder):
                msg_status(_('Folder not found: {}').format(folder))
                return
            attempts = terminal_attempts(OS_PLATFORM, folder)
            if not attempts:
                msg_status(_('Open Terminal Here is not implemented for this OS'))
                return
            self._run_first(attempts, _('Could not open a terminal'))
        except Exception:
            _log_error('open_terminal')

    def _reload(self, editor):
        try:
            path = self._require_saved(editor)
            if not path:
                return
            try:
                editor.focus()
            except Exception:
                pass
            editor.cmd(cmd_FileReopen)
        except Exception:
            _log_error('reload')

    def _initial_save_location(self, editor):
        path = editor.get_filename()
        if is_saved_file(path):
            absolute = os.path.abspath(path)
            return os.path.dirname(absolute), os.path.basename(absolute)
        title = (editor.get_prop(PROP_TAB_TITLE) or '').lstrip('*').strip()
        return os.path.expanduser('~'), title or 'untitled.txt'

    def _write_tab_copy(self, editor, dest, overwrite):
        dest = prepare_destination(dest, overwrite=overwrite)
        saved = None
        try:
            saved = editor.save(dest, True)
        except TypeError:
            saved = None
        except Exception:
            _log_error('editor.save copy')
            saved = False
        if saved:
            return dest
        if saved is None:
            text = editor.get_text_all() or ''
            encoding = editor.get_prop(PROP_ENC) or ''
            newline = editor.get_prop(PROP_NEWLINE) or 'lf'
            data = encode_document(text, encoding, newline=newline)
            return safe_write_bytes(dest, data, overwrite=True)
        raise FileOpError(_('Could not write {}').format(dest))

    def _save_copy(self, editor):
        try:
            init_dir, init_name = self._initial_save_location(editor)
            chosen = dlg_file(False, init_name, init_dir, _('All files|*.*'), _('Save a Copy As'))
            dest = first_path(chosen)
            if not dest:
                return
            current = editor.get_filename()
            if current and os.path.normcase(os.path.abspath(current)) == os.path.normcase(os.path.abspath(dest)):
                msg_status(_('That is this tab\'s file. Use Save to update it.'))
                return
            written = self._write_tab_copy(editor, dest, overwrite=True)
            msg_status(_('Saved a copy to {}').format(written))
        except FileOpError as ex:
            msg_status(str(ex))
        except Exception:
            _log_error('save_copy')

    def _duplicate(self, editor):
        try:
            path = self._require_saved(editor)
            if not path:
                return
            folder = os.path.dirname(path)
            base = os.path.basename(path)

            def exists(name):
                return os.path.exists(os.path.join(folder, name))

            suggested = suggest_duplicate_name(base, exists)
            entered = dlg_input(_('Duplicate file as (same folder):\n{}').format(folder), suggested)
            if entered is None:
                return
            name = clean_duplicate_basename(entered)
            dest = os.path.join(folder, name)
            if os.path.normcase(os.path.abspath(dest)) == os.path.normcase(path):
                msg_status(_('Choose a different file name'))
                return
            overwrite = False
            if os.path.exists(dest):
                if msg_box(
                    _('Overwrite existing file?\n\n{}').format(dest),
                    MB_OKCANCEL + MB_ICONWARNING,
                ) != ID_OK:
                    return
                overwrite = True
            modified = bool(editor.get_prop(PROP_MODIFIED))
            if modified:
                written = self._write_tab_copy(editor, dest, overwrite=overwrite)
            else:
                written = safe_copy_file(path, dest, overwrite=overwrite)
            file_open(written)
            msg_status(_('Opened duplicate {}').format(written))
        except FileOpError as ex:
            msg_status(str(ex))
        except Exception:
            _log_error('duplicate')

    def _close_and_delete(self, editor):
        try:
            path = self._require_saved(editor)
            if not path:
                return
            question = _('Close this tab and permanently delete this file from disk?\n\n{}').format(path)
            if editor.get_prop(PROP_MODIFIED):
                question += _('\n\nUnsaved changes in the tab will be discarded.')
            if msg_box(question, MB_OKCANCEL + MB_ICONWARNING) != ID_OK:
                return
            if editor.get_prop(PROP_MODIFIED):
                editor.set_prop(PROP_MODIFIED, False)
            try:
                editor.focus()
            except Exception:
                pass
            editor.cmd(cmd_FileClose)
            safe_delete_file(path)
            msg_status(_('Deleted {}').format(path))
        except FileOpError as ex:
            msg_status(str(ex))
        except Exception:
            _log_error('close_delete')

    def _export_html(self, editor):
        try:
            if not is_text_document(editor):
                msg_status(_('Not a text document'))
                return
            try:
                editor.focus()
            except Exception:
                pass
            editor.cmd(cmd_FileExportHtml)
        except Exception:
            _log_error('export_html')

    def _lexer_name(self, editor):
        lex = editor.get_prop(PROP_LEXER_FILE)
        if not lex:
            return CAP_NONE
        if lex.endswith(' ^'):
            lex = lex[:-2]
        return lex

    def _build_info(self, editor):
        path = editor.get_filename()
        on_disk = is_saved_file(path)
        modified = bool(editor.get_prop(PROP_MODIFIED))
        try:
            read_only = bool(editor.get_prop(PROP_RO))
        except Exception:
            read_only = False

        if on_disk:
            file_path = os.path.abspath(path)
            file_name = os.path.basename(file_path)
        else:
            file_path = CAP_UNSAVED
            title = (editor.get_prop(PROP_TAB_TITLE) or '').lstrip('*').strip()
            file_name = title or CAP_UNSAVED

        encoding = editor.get_prop(PROP_ENC) or CAP_NONE
        try:
            endings = format_line_endings(editor.get_prop(PROP_NEWLINE))
        except Exception:
            endings = CAP_NONE

        info = {
            'path': file_path,
            'filename': file_name,
            'status': format_status(on_disk, modified, read_only),
            'encoding': encoding,
            'line_endings': endings,
            'lexer': self._lexer_name(editor),
        }

        text = None
        if on_disk:
            try:
                info['size_disk'] = format_size(os.path.getsize(path))
            except OSError:
                info['size_disk'] = CAP_NONE
            try:
                info['modified'] = format_timestamp(os.path.getmtime(path))
            except OSError:
                info['modified'] = CAP_NONE

        if modified or not on_disk or is_text_document(editor):
            text = editor.get_text_all() or ''

        if modified or not on_disk:
            payload = text if text is not None else (editor.get_text_all() or '')
            info['size_memory'] = format_size(len(payload.encode('utf-8')))

        if is_text_document(editor):
            info['lines'] = str(editor.get_line_count())
            if text is None:
                text = editor.get_text_all() or ''
            info['words'] = str(count_words(text))
            info['characters'] = str(count_characters(text))

        return info

    def _show_info(self, editor):
        spec = build_file_info_dialog(
            self._build_info(editor),
            _ui_theme_dict(),
            captions={
                'close': button_ex_label(_('Close')),
                'copy': button_ex_label(_('Copy Info')),
                'unsaved': _('(Unsaved)'),
            },
        )
        self._dialog_text = spec['copy_text']
        dlg = dlg_proc(0, DLG_CREATE)
        dlg_proc(dlg, DLG_PROP_SET, prop={
            'cap': CAP_DIALOG,
            'w': spec['width'],
            'h': spec['height'],
            'w_min': spec['min_width'],
            'h_min': spec['min_height'],
            'border': DBORDER_SIZE,
            'color': spec['palette']['background'],
            # Form KeyDown sees Escape only when keypreview is on. TFormDummy
            # then closes a modal dialog. Our handler hides on Escape too.
            'keypreview': bool(spec.get('keypreview')),
            'on_key_down': self._info_key_down,
        })
        try:
            for control in spec['controls']:
                prop = dict(control['prop'])
                role = control.get('role')
                if role == 'close':
                    prop['on_change'] = self._info_close
                elif role == 'copy':
                    prop['on_change'] = self._info_copy
                index = dlg_proc(dlg, DLG_CTL_ADD, prop=control['type'])
                dlg_proc(dlg, DLG_CTL_PROP_SET, index=index, prop=prop)
                if control.get('focusable'):
                    # Constructor sets Focusable without the Qt5 ControlStyle
                    # update. BTN_SET_FOCUSABLE runs SetFocusable so Close can
                    # take focus on Qt5.
                    handle = dlg_proc(dlg, DLG_CTL_HANDLE, index=index)
                    if handle:
                        button_proc(handle, BTN_SET_FOCUSABLE, '1')
            dlg_proc(dlg, DLG_CTL_FOCUS, name='btn_close')
            dlg_proc(dlg, DLG_SCALE)
            dlg_proc(dlg, DLG_SHOW_MODAL)
        finally:
            dlg_proc(dlg, DLG_FREE)

    def _info_key_down(self, id_dlg, id_ctl, data=''):
        # False blocks the key. Ctrl+C is not a dialog command, so the path
        # edit still copies its selection. Enter is left to the focused
        # button_ex, which clicks itself.
        if file_info_key_action(id_ctl, data) == 'close':
            dlg_proc(id_dlg, DLG_HIDE)
            return False
        return True

    def _info_close(self, id_dlg, id_ctl, data='', info=''):
        dlg_proc(id_dlg, DLG_HIDE)

    def _info_copy(self, id_dlg, id_ctl, data='', info=''):
        app_proc(PROC_SET_CLIP, self._dialog_text)
        msg_status(_('File info copied'))

    def _file_info(self, editor):
        try:
            self._show_info(editor)
        except Exception:
            _log_error('file_info')

    def menu_file_info(self, info=''):
        self._file_info(self._current_ed(prefer_tab=True))

    def menu_reveal(self, info=''):
        self._reveal(self._current_ed(prefer_tab=True))

    def menu_open_folder(self, info=''):
        self._open_folder(self._current_ed(prefer_tab=True))

    def menu_terminal(self, info=''):
        self._open_terminal(self._current_ed(prefer_tab=True))

    def menu_reload(self, info=''):
        self._reload(self._current_ed(prefer_tab=True))

    def menu_save_copy(self, info=''):
        self._save_copy(self._current_ed(prefer_tab=True))

    def menu_duplicate(self, info=''):
        self._duplicate(self._current_ed(prefer_tab=True))

    def menu_close_delete(self, info=''):
        self._close_and_delete(self._current_ed(prefer_tab=True))

    def menu_export_html(self, info=''):
        self._export_html(self._current_ed(prefer_tab=True))

    def cmd_file_info(self, info=''):
        self._file_info(self._current_ed(prefer_tab=False))

    def cmd_reveal(self, info=''):
        self._reveal(self._current_ed(prefer_tab=False))

    def cmd_open_folder(self, info=''):
        self._open_folder(self._current_ed(prefer_tab=False))

    def cmd_open_terminal(self, info=''):
        self._open_terminal(self._current_ed(prefer_tab=False))

    def cmd_reload(self, info=''):
        self._reload(self._current_ed(prefer_tab=False))

    def cmd_save_copy(self, info=''):
        self._save_copy(self._current_ed(prefer_tab=False))

    def cmd_duplicate(self, info=''):
        self._duplicate(self._current_ed(prefer_tab=False))

    def cmd_close_delete(self, info=''):
        self._close_and_delete(self._current_ed(prefer_tab=False))

    def cmd_export_html(self, info=''):
        self._export_html(self._current_ed(prefer_tab=False))
