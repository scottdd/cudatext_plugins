import os
import shutil
import subprocess
import sys
import traceback

__version__ = '0.7.0'

from cudatext import *
from cudatext_cmd import cmd_FileClose, cmd_FileExportHtml, cmd_FileReopen
from cudax_lib import get_translation

from .logic import (
    FileOpError,
    available_attempts,
    clean_duplicate_basename,
    count_characters,
    count_words,
    encode_document,
    first_path,
    format_file_info,
    format_line_endings,
    format_size,
    format_status,
    format_timestamp,
    open_folder_attempts,
    platform_from_suffix,
    prepare_destination,
    reveal_attempts,
    safe_copy_file,
    safe_delete_file,
    safe_write_bytes,
    suggest_duplicate_name,
    terminal_attempts,
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

    def _add_item(self, parent_id, key, caption, command, enabled):
        item_id = menu_proc(
            parent_id,
            MENU_ADD,
            caption=caption,
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
            self._add_item(tab_id, 'info', CAP_FILE_INFO, self.menu_file_info, True)
            self._add_item(tab_id, 'reveal', CAP_REVEAL, self.menu_reveal, saved)
            self._add_item(tab_id, 'folder', CAP_OPEN_FOLDER, self.menu_open_folder, saved)
            self._add_item(tab_id, 'terminal', CAP_TERMINAL, self.menu_terminal, saved)
            self._add_item(tab_id, 'reload', CAP_RELOAD, self.menu_reload, saved)
            self._add_item(tab_id, 'savecopy', CAP_SAVE_COPY, self.menu_save_copy, True)
            self._add_item(tab_id, 'duplicate', CAP_DUPLICATE, self.menu_duplicate, saved)
            self._add_item(tab_id, 'delete', CAP_DELETE, self.menu_close_delete, saved)
            self._add_item(tab_id, 'html', CAP_EXPORT, self.menu_export_html, text_doc)
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

        return format_file_info(info)

    def _show_info(self, editor):
        text = self._build_info(editor)
        self._dialog_text = text
        w = 560
        h = 360
        dlg = dlg_proc(0, DLG_CREATE)
        dlg_proc(dlg, DLG_PROP_SET, prop={
            'cap': CAP_DIALOG,
            'w': w,
            'h': h,
            'w_min': 380,
            'h_min': 200,
            'border': DBORDER_SIZE,
        })

        btn_close = dlg_proc(dlg, DLG_CTL_ADD, prop='button')
        dlg_proc(dlg, DLG_CTL_PROP_SET, index=btn_close, prop={
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
            'on_change': self._info_close,
            'ex0': True,
        })

        btn_copy = dlg_proc(dlg, DLG_CTL_ADD, prop='button')
        dlg_proc(dlg, DLG_CTL_PROP_SET, index=btn_copy, prop={
            'name': 'btn_copy',
            'cap': _('&Copy Info'),
            'a_l': None,
            'a_t': None,
            'a_r': ('btn_close', '['),
            'a_b': ('', ']'),
            'sp_r': 6,
            'sp_b': 6,
            'x': w - 210,
            'y': h - 6 - 25,
            'w': 104,
            'on_change': self._info_copy,
        })

        memo = dlg_proc(dlg, DLG_CTL_ADD, prop='memo')
        dlg_proc(dlg, DLG_CTL_PROP_SET, index=memo, prop={
            'name': 'memo_info',
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
