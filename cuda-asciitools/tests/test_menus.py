"""Hotkeys, tab submenu targeting, and shared tab-popup handle.

CudaText is not running. A stand-in menu_proc models the dangerous case:
every access to the string id 'tab' rebuilds the stock popup and drops
plugin items, keeping the same numeric id. Current CudaText creates that
popup only once; the stand-in still wipes, so a lazy resolve during
on_tab_menu fails this test.
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from logic import (
    caption_with_hotkey,
    is_chord_hotkey,
    lookup_command_hotkey,
    primary_hotkey,
    shortcut_for_menu,
    tab_handle_from_prop,
    usable_menu_handle,
)


REPO = Path(__file__).resolve().parents[2]
PLUGIN_DIR = Path(__file__).resolve().parents[1]
ASCII_DIR = REPO / 'cuda-asciitools'
TAB_DIR = REPO / 'cuda-tabmenu'
IS_ASCII = (PLUGIN_DIR / 'anyascii').is_dir()

MENU_CLEAR = 0
MENU_ENUM = 1
MENU_ADD = 2
MENU_REMOVE = 3
MENU_SET_ENABLED = 6
MENU_GET_PROP = 14
PROC_GET_OS_SUFFIX = 2
PROC_GET_FINDER_PROP = 36
PROC_GET_HOTKEY = 41
PROC_SET_CLIP = 1
APPSTATE_CONFIG_REREAD = 24
PROP_RO = 6
PROP_KIND = 59
PROP_HANDLE_SELF = 110


class EdBox:
    """Stable `ed` object. The plugin binds this name at import."""

    def __init__(self):
        self.current = None

    def __getattr__(self, name):
        return getattr(self.current, name)


class Editor:
    def __init__(self, kind='text', handle=1, filename='', lines=None):
        self.props = {
            PROP_KIND: kind,
            PROP_HANDLE_SELF: handle,
            PROP_RO: False,
        }
        self.filename = filename
        self.lines = list(lines if lines is not None else ['abc'])
        self.carets = [(0, 0, -1, -1)]
        self.focused = 0
        self.caret_set = None

    def get_prop(self, key):
        return self.props.get(key, '')

    def get_filename(self):
        return self.filename

    def get_carets(self):
        return self.carets

    def get_line_count(self):
        return len(self.lines)

    def get_text_line(self, index):
        return self.lines[index]

    def set_caret(self, *args):
        self.caret_set = args

    def focus(self):
        self.focused += 1

    def attr(self, *args, **kwargs):
        return []


class MenuWorld:
    """menu_proc stand-in.

    wipe_on_tab_string models older InitPopupTab: the string id rebuilds the
    popup and drops plugin items. The numeric id stays. A later access with
    that number does not rebuild.
    """

    def __init__(self, wipe_on_tab_string=True):
        self.wipe_on_tab_string = wipe_on_tab_string
        self.next_id = 1
        self.nodes = {}
        self.kids = {}
        self.popup_id = None
        self.top_sr = self._new('Search')
        self.string_tab_calls = 0
        self.calls = []
        self.hotkeys = {}
        self.raise_hotkey = False
        self.ed = EdBox()

    def _new(self, cap='', tag='', command=None, parent=None):
        nid = self.next_id
        self.next_id += 1
        self.nodes[nid] = {
            'id': nid,
            'cap': cap,
            'tag': tag or '',
            'command': command,
            'en': True,
            'parent': parent,
        }
        self.kids[nid] = []
        if parent is not None:
            self.kids[parent].append(nid)
        return nid

    def _delete_tree(self, nid):
        for child in list(self.kids.get(nid, [])):
            self._delete_tree(child)
        self.kids.pop(nid, None)
        self.nodes.pop(nid, None)

    def _ensure_popup(self):
        if self.popup_id is None:
            self.popup_id = self._new('tab-root')
            self._new('Close tab', tag='stock_close', parent=self.popup_id)
            return
        if not self.wipe_on_tab_string:
            return
        survivors = []
        for child in list(self.kids.get(self.popup_id, [])):
            tag = self.nodes[child]['tag']
            if tag.startswith('cuda_tabmenu_') or tag.startswith('cuda_asciitools_'):
                self._delete_tree(child)
            else:
                survivors.append(child)
        self.kids[self.popup_id] = survivors

    def resolve(self, menu_id):
        if menu_id == 'tab':
            self.string_tab_calls += 1
            self._ensure_popup()
            return self.popup_id
        if menu_id == 'top-sr':
            return self.top_sr
        if isinstance(menu_id, str) and menu_id.isdigit():
            return int(menu_id)
        return menu_id

    def children(self, parent):
        parent = self.resolve(parent)
        return [self.nodes[cid] for cid in self.kids.get(parent, [])]

    def menu_proc(self, menu_id, action, **kwargs):
        self.calls.append((menu_id, action, dict(kwargs)))
        parent = self.resolve(menu_id)
        if action == MENU_ENUM:
            listed = []
            for node in self.children(parent):
                item = {'id': node['id'], 'cap': node['cap']}
                if node['tag']:
                    item['tag'] = node['tag']
                if not node['en']:
                    item['en'] = False
                listed.append(item)
            return listed
        if action == MENU_GET_PROP:
            node = self.nodes.get(parent)
            if node is None:
                return None
            return {'id': parent, 'cap': node['cap']}
        if action == MENU_ADD:
            nid = self._new(
                kwargs.get('caption', ''),
                tag=kwargs.get('tag', ''),
                command=kwargs.get('command'),
                parent=parent,
            )
            return str(nid)
        if action == MENU_REMOVE:
            node = self.nodes.get(parent)
            owner = node['parent'] if node else None
            self._delete_tree(parent)
            if owner is not None and owner in self.kids:
                self.kids[owner] = [cid for cid in self.kids[owner] if cid != parent]
            return None
        if action == MENU_CLEAR:
            for child in list(self.kids.get(parent, [])):
                self._delete_tree(child)
            self.kids[parent] = []
            return None
        if action == MENU_SET_ENABLED:
            self.nodes[parent]['en'] = bool(kwargs.get('command'))
            return None
        return None


def install_fakes(world):
    cudatext = types_module('cudatext')
    cudatext.MENU_CLEAR = MENU_CLEAR
    cudatext.MENU_ENUM = MENU_ENUM
    cudatext.MENU_ADD = MENU_ADD
    cudatext.MENU_REMOVE = MENU_REMOVE
    cudatext.MENU_SET_ENABLED = MENU_SET_ENABLED
    cudatext.MENU_GET_PROP = MENU_GET_PROP
    cudatext.PROC_GET_OS_SUFFIX = PROC_GET_OS_SUFFIX
    cudatext.PROC_GET_FINDER_PROP = PROC_GET_FINDER_PROP
    cudatext.PROC_GET_HOTKEY = PROC_GET_HOTKEY
    cudatext.PROC_SET_CLIP = PROC_SET_CLIP
    cudatext.APPSTATE_CONFIG_REREAD = APPSTATE_CONFIG_REREAD
    cudatext.PROP_RO = PROP_RO
    cudatext.PROP_KIND = PROP_KIND
    cudatext.PROP_HANDLE_SELF = PROP_HANDLE_SELF
    cudatext.ed = world.ed

    def app_proc(proc_id, text=''):
        if proc_id == PROC_GET_OS_SUFFIX:
            return ''
        if proc_id == PROC_GET_FINDER_PROP:
            return {'op_wrap': False}
        if proc_id == PROC_GET_HOTKEY:
            if world.raise_hotkey:
                raise RuntimeError('PROC_GET_HOTKEY unavailable')
            return world.hotkeys.get(text, '')
        return ''

    def menu_proc(menu_id, action, command='', caption='', index=-1, hotkey='', tag=''):
        # The real signature always has hotkey. Plugins that omit it still
        # pass the default through a Python binding. Detect an explicit pass
        # by wrapping below; this signature is only the fallback.
        raise AssertionError('menu_proc must be called through the wrapper')

    def menu_proc_wrapper(menu_id, action, **kwargs):
        return world.menu_proc(menu_id, action, **kwargs)

    cudatext.app_proc = app_proc
    cudatext.menu_proc = menu_proc_wrapper
    cudatext.msg_status = lambda *args, **kwargs: None
    cudatext.msg_box = lambda *args, **kwargs: 0
    cudatext.dlg_proc = lambda *args, **kwargs: None
    cudatext.file_open = lambda *args, **kwargs: False
    sys.modules['cudatext'] = cudatext

    cudax = types_module('cudax_lib')
    cudax.get_translation = lambda path: (lambda text: text)
    sys.modules['cudax_lib'] = cudax

    cmds = types_module('cudatext_cmd')
    cmds.cmd_FileClose = 1
    cmds.cmd_FileExportHtml = 2
    cmds.cmd_FileReopen = 3
    sys.modules['cudatext_cmd'] = cmds
    return world


def types_module(name):
    import types
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module


_LOAD_SEQ = 0


def load_plugin(folder, prefix):
    global _LOAD_SEQ
    _LOAD_SEQ += 1
    pkg = '%s_%d' % (prefix, _LOAD_SEQ)
    init = folder / '__init__.py'
    spec = importlib.util.spec_from_file_location(
        pkg,
        init,
        submodule_search_locations=[str(folder)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[pkg] = module
    spec.loader.exec_module(module)
    return module


def passed_hotkeys(world):
    found = []
    for _menu_id, _action, kwargs in world.calls:
        if 'hotkey' in kwargs:
            found.append(kwargs['hotkey'])
    return found


class HotkeyParseTests(unittest.TestCase):
    def test_primary_is_the_first_slot(self):
        self.assertEqual(primary_hotkey('Alt+F3|Ctrl+Shift+N'), 'Alt+F3')
        self.assertEqual(primary_hotkey('Alt+F3|'), 'Alt+F3')
        self.assertEqual(primary_hotkey('  Alt+Shift+F3  |Ctrl+N'), 'Alt+Shift+F3')

    def test_empty_primary_is_not_the_secondary(self):
        self.assertEqual(primary_hotkey('|Ctrl+N'), '')
        self.assertEqual(primary_hotkey('|'), '')
        self.assertEqual(primary_hotkey(''), '')
        self.assertEqual(primary_hotkey(None), '')
        self.assertEqual(primary_hotkey(12), '')

    def test_chords_are_detected_and_omitted_from_shortcut(self):
        self.assertTrue(is_chord_hotkey('Ctrl+K * Ctrl+A'))
        self.assertTrue(is_chord_hotkey('Ctrl+B*B'))
        self.assertFalse(is_chord_hotkey('Alt+F3'))
        self.assertFalse(is_chord_hotkey(''))
        self.assertFalse(is_chord_hotkey(None))
        self.assertEqual(shortcut_for_menu('Ctrl+K * Ctrl+A|Ctrl+K * B'), '')
        self.assertEqual(shortcut_for_menu('Ctrl+B * B|'), '')
        self.assertEqual(shortcut_for_menu('Alt+F3|Ctrl+Shift+N'), 'Alt+F3')
        self.assertEqual(shortcut_for_menu(''), '')
        self.assertEqual(shortcut_for_menu(None), '')

    def test_caption_shows_primary_and_chord_without_a_second_slot(self):
        self.assertEqual(caption_with_hotkey('Next', 'Alt+F3|Ctrl+N'), 'Next\tAlt+F3')
        self.assertEqual(
            caption_with_hotkey('List', 'Ctrl+K * Ctrl+A|'),
            'List\tCtrl+K * Ctrl+A',
        )
        self.assertEqual(caption_with_hotkey('Highlight', ''), 'Highlight')
        self.assertEqual(caption_with_hotkey('Highlight', None), 'Highlight')
        self.assertEqual(caption_with_hotkey('Highlight', '|Ctrl+H'), 'Highlight')

    def test_lookup_degrades_when_the_api_raises_or_is_empty(self):
        def raise_hotkey(_command_id):
            raise RuntimeError('missing')

        self.assertEqual(lookup_command_hotkey(raise_hotkey, 'cuda_asciitools,menu_next_nonascii'), '')
        self.assertEqual(lookup_command_hotkey(lambda _cid: None, 'm,c'), '')
        self.assertEqual(
            lookup_command_hotkey(lambda _cid: 'F2|F3', 'cuda_tabmenu,cmd_file_info'),
            'F2',
        )

    def test_absent_tab_handles(self):
        self.assertIsNone(usable_menu_handle(None))
        self.assertIsNone(usable_menu_handle(''))
        self.assertIsNone(usable_menu_handle(0))
        self.assertIsNone(usable_menu_handle('0'))
        self.assertIsNone(usable_menu_handle('tab'))
        self.assertEqual(usable_menu_handle(42), 42)
        self.assertEqual(tab_handle_from_prop({'id': 7}), 7)
        self.assertIsNone(tab_handle_from_prop({'id': 'tab'}))
        self.assertIsNone(tab_handle_from_prop(None))
        self.assertIsNone(tab_handle_from_prop('tab'))


class StringIdWipeTests(unittest.TestCase):
    def test_second_string_access_drops_plugin_items(self):
        world = MenuWorld(wipe_on_tab_string=True)
        root = world.menu_proc('tab', MENU_GET_PROP)['id']
        world.menu_proc(root, MENU_ADD, caption='Info', tag='cuda_tabmenu_item_info')
        world.menu_proc('tab', MENU_GET_PROP)
        tags = [node['tag'] for node in world.children(world.popup_id)]
        self.assertNotIn('cuda_tabmenu_item_info', tags)
        self.assertIn('stock_close', tags)

    def test_current_create_once_behavior_keeps_items(self):
        world = MenuWorld(wipe_on_tab_string=False)
        root = world.menu_proc('tab', MENU_GET_PROP)['id']
        world.menu_proc(root, MENU_ADD, caption='Info', tag='cuda_tabmenu_item_info')
        again = world.menu_proc('tab', MENU_GET_PROP)['id']
        self.assertEqual(again, root)
        tags = [node['tag'] for node in world.children(world.popup_id)]
        self.assertIn('cuda_tabmenu_item_info', tags)


class SharedTabHandleTests(unittest.TestCase):
    def _plugins(self):
        world = MenuWorld(wipe_on_tab_string=True)
        install_fakes(world)
        ascii_mod = load_plugin(ASCII_DIR, 'ascii_plugin')
        tab_mod = load_plugin(TAB_DIR, 'tab_plugin')
        return world, ascii_mod.Command(), tab_mod.Command()

    def test_either_startup_order_keeps_both_menus_on_the_first_click(self):
        orders = (('ascii', 'tab'), ('tab', 'ascii'))
        for order in orders:
            with self.subTest(order=order):
                world, ascii_cmd, tab_cmd = self._plugins()
                commands = {'ascii': ascii_cmd, 'tab': tab_cmd}
                for name in order:
                    commands[name].on_start(None)
                self.assertEqual(world.string_tab_calls, 2)
                self.assertEqual(ascii_cmd._tab_menu_handle, tab_cmd._tab_menu_handle)
                self.assertEqual(ascii_cmd._tab_menu_handle, world.popup_id)

                editor = Editor(lines=['aé'])
                world.ed.current = Editor(lines=['xyz'], handle=9)
                before = world.string_tab_calls
                for name in order:
                    commands[name].on_tab_menu(editor)
                self.assertEqual(world.string_tab_calls, before)

                tags = [node['tag'] for node in world.children(world.popup_id)]
                self.assertIn('stock_close', tags)
                self.assertIn('cuda_tabmenu_item_info', tags)
                self.assertIn('cuda_tabmenu_item_html', tags)
                self.assertIn('cuda_asciitools_tab_sep', tags)
                self.assertIn('cuda_asciitools_tab_menu', tags)
                self.assertEqual(passed_hotkeys(world), [])

    def test_rebuilding_one_plugin_does_not_drop_the_other(self):
        world, ascii_cmd, tab_cmd = self._plugins()
        editor = Editor()
        ascii_cmd.on_start(None)
        tab_cmd.on_start(None)
        ascii_cmd.on_tab_menu(editor)
        tab_cmd.on_tab_menu(editor)
        ascii_cmd.on_tab_menu(editor)
        tags = [node['tag'] for node in world.children(world.popup_id)]
        self.assertEqual(tags.count('cuda_asciitools_tab_menu'), 1)
        self.assertIn('cuda_tabmenu_item_reveal', tags)
        self.assertIn('stock_close', tags)


class AsciiMenuTests(unittest.TestCase):
    def setUp(self):
        if not IS_ASCII:
            self.skipTest('ASCII Tools suite')
        self.world = MenuWorld(wipe_on_tab_string=True)
        install_fakes(self.world)
        self.world.hotkeys = {
            'cuda_asciitools,menu_next_nonascii': 'Alt+F3|',
            'cuda_asciitools,menu_prev_nonascii': 'Alt+Shift+F3|Ctrl+Shift+N',
            'cuda_asciitools,menu_list_nonascii': 'Ctrl+K * Ctrl+A|',
            'cuda_asciitools,menu_highlight_nonascii': '|Ctrl+H',
        }
        self.mod = load_plugin(ASCII_DIR, 'ascii_only')
        self.cmd = self.mod.Command()
        self.active = Editor(lines=['xé'], handle=1)
        self.clicked = Editor(lines=['aé'], handle=2)
        self.world.ed.current = self.active

    def _submenu(self, parent, tag):
        for node in self.world.children(parent):
            if node['tag'] == tag:
                return node
        self.fail('missing submenu %s' % tag)

    def test_search_and_tab_menus_show_live_hotkeys_without_shortcut_prop(self):
        self.cmd.on_init_plugins_menu(None)
        self.cmd.on_start(None)
        self.cmd.on_tab_menu(self.clicked)
        self.assertEqual(passed_hotkeys(self.world), [])

        search = self._submenu(self.world.top_sr, 'cuda_asciitools_search')
        tab = self._submenu(self.world.popup_id, 'cuda_asciitools_tab_menu')
        search_caps = [node['cap'] for node in self.world.children(search['id'])]
        tab_caps = [node['cap'] for node in self.world.children(tab['id'])]
        self.assertEqual(search_caps, tab_caps)
        self.assertIn('Next Non-ASCII Character\tAlt+F3', search_caps)
        self.assertIn('Previous Non-ASCII Character\tAlt+Shift+F3', search_caps)
        self.assertIn('List Non-ASCII Characters\tCtrl+K * Ctrl+A', search_caps)
        self.assertIn('Highlight Non-ASCII', search_caps)
        self.assertNotIn('Highlight Non-ASCII\tCtrl+H', search_caps)
        self.assertEqual(search_caps.count('-'), 3)
        self.assertTrue(tab['en'])

    def test_tab_command_uses_the_clicked_tab(self):
        self.cmd.on_start(None)
        self.cmd.on_tab_menu(self.clicked)
        tab = self._submenu(self.world.popup_id, 'cuda_asciitools_tab_menu')
        nxt = next(node for node in self.world.children(tab['id']) if node['cap'].startswith('Next'))
        nxt['command']()
        self.assertEqual(self.clicked.focused, 1)
        self.assertEqual(self.clicked.caret_set[0], 1)
        self.assertEqual(self.active.focused, 0)
        self.assertIsNone(self.active.caret_set)

        self.cmd._tab_ed = self.clicked
        self.cmd.menu_next_nonascii()
        self.assertEqual(self.active.focused, 1)
        self.assertEqual(self.clicked.focused, 1)

    def test_non_text_tab_disables_the_submenu(self):
        self.cmd.on_start(None)
        binary = Editor(kind='viewer', handle=4)
        self.cmd.on_tab_menu(binary)
        tab = self._submenu(self.world.popup_id, 'cuda_asciitools_tab_menu')
        self.assertFalse(tab['en'])
        self.assertTrue(self.world.children(tab['id']))

    def test_search_menu_refreshes_when_focus_returns_or_config_is_reread(self):
        self.cmd.on_init_plugins_menu(None)
        clears = [call for call in self.world.calls if call[1] == MENU_CLEAR]
        self.cmd.on_focus(None)
        self.assertEqual([call for call in self.world.calls if call[1] == MENU_CLEAR], clears)

        self.world.hotkeys['cuda_asciitools,menu_next_nonascii'] = 'F8|'
        self.cmd.on_focus(None)
        search = self._submenu(self.world.top_sr, 'cuda_asciitools_search')
        caps = [node['cap'] for node in self.world.children(search['id'])]
        self.assertIn('Next Non-ASCII Character\tF8', caps)

        self.world.hotkeys['cuda_asciitools,menu_next_nonascii'] = 'F2|'
        self.cmd.on_state(None, 1)
        caps = [node['cap'] for node in self.world.children(search['id'])]
        self.assertIn('Next Non-ASCII Character\tF8', caps)
        self.cmd.on_state(None, APPSTATE_CONFIG_REREAD)
        caps = [node['cap'] for node in self.world.children(search['id'])]
        self.assertIn('Next Non-ASCII Character\tF2', caps)

    def test_missing_hotkey_api_leaves_captions_plain(self):
        self.world.raise_hotkey = True
        self.cmd.on_init_plugins_menu(None)
        self.cmd.on_start(None)
        self.cmd.on_tab_menu(self.clicked)
        search = self._submenu(self.world.top_sr, 'cuda_asciitools_search')
        for node in self.world.children(search['id']):
            self.assertNotIn('\t', node['cap'])
        self.assertEqual(passed_hotkeys(self.world), [])


class TabMenuHotkeyTests(unittest.TestCase):
    def setUp(self):
        if IS_ASCII:
            self.skipTest('Tab Menu suite')
        self.world = MenuWorld(wipe_on_tab_string=True)
        install_fakes(self.world)
        self.world.hotkeys = {
            'cuda_tabmenu,cmd_file_info': 'Ctrl+Shift+Alt+I|',
            'cuda_tabmenu,cmd_reveal': 'Ctrl+K * R|Ctrl+Alt+R',
            'cuda_tabmenu,cmd_duplicate': '|Ctrl+D',
        }
        self.mod = load_plugin(TAB_DIR, 'tab_only')
        self.cmd = self.mod.Command()

    def _by_tag(self, tag):
        for node in self.world.children(self.world.popup_id):
            if node['tag'] == tag:
                return node
        self.fail(tag)

    def test_nine_items_show_primary_or_chord_and_no_shortcut_prop(self):
        self.cmd.on_start(None)
        editor = Editor()
        self.cmd.on_tab_menu(editor)
        self.assertEqual(passed_hotkeys(self.world), [])
        info = self._by_tag('cuda_tabmenu_item_info')
        reveal = self._by_tag('cuda_tabmenu_item_reveal')
        duplicate = self._by_tag('cuda_tabmenu_item_duplicate')
        folder = self._by_tag('cuda_tabmenu_item_folder')
        self.assertEqual(info['cap'], 'File &Info...\tCtrl+Shift+Alt+I')
        self.assertEqual(reveal['cap'], '&Reveal in File Manager\tCtrl+K * R')
        self.assertEqual(duplicate['cap'], 'D&uplicate File')
        self.assertNotIn('\t', folder['cap'])
        tags = [node['tag'] for node in self.world.children(self.world.popup_id)]
        for key in (
            'info', 'reveal', 'folder', 'terminal', 'reload',
            'savecopy', 'duplicate', 'delete', 'html',
        ):
            self.assertIn('cuda_tabmenu_item_' + key, tags)

    def test_unsaved_and_non_text_disable_the_same_items(self):
        self.cmd.on_start(None)
        self.cmd.on_tab_menu(Editor(kind='viewer'))
        self.assertTrue(self._by_tag('cuda_tabmenu_item_info')['en'])
        self.assertTrue(self._by_tag('cuda_tabmenu_item_savecopy')['en'])
        self.assertFalse(self._by_tag('cuda_tabmenu_item_reveal')['en'])
        self.assertFalse(self._by_tag('cuda_tabmenu_item_html')['en'])

        with tempfile.NamedTemporaryFile() as handle:
            self.cmd.on_tab_menu(Editor(filename=handle.name))
        self.assertTrue(self._by_tag('cuda_tabmenu_item_reveal')['en'])
        self.assertTrue(self._by_tag('cuda_tabmenu_item_html')['en'])

    def test_missing_hotkey_api_leaves_captions_plain(self):
        self.world.raise_hotkey = True
        self.cmd.on_start(None)
        self.cmd.on_tab_menu(Editor())
        for node in self.world.children(self.world.popup_id):
            self.assertNotIn('\t', node['cap'])
        self.assertEqual(passed_hotkeys(self.world), [])

    def test_plugins_command_ignores_the_clicked_tab(self):
        active = Editor(filename='', handle=1)
        clicked = Editor(filename='', handle=2)
        self.world.ed.current = active
        self.cmd.on_start(None)
        self.cmd.on_tab_menu(clicked)
        self.assertIs(self.cmd._current_ed(prefer_tab=True), clicked)
        self.assertIs(self.cmd._current_ed(prefer_tab=False), self.world.ed)
        self.assertIs(self.world.ed.current, active)


if __name__ == '__main__':
    unittest.main()
