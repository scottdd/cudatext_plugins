import subprocess
import unittest
from pathlib import Path


PLUGIN_DIR = Path(__file__).resolve().parents[1]
ZIP_PATH = PLUGIN_DIR / 'dist' / 'plugin.Tab_Menu.zip'


def _version_from(path, prefix):
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith(prefix):
            return line.split('=', 1)[1].strip().strip('\'"')
    raise AssertionError('missing %s in %s' % (prefix, path))


class PackScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(
            ['bash', str(PLUGIN_DIR / 'pack.sh')],
            cwd=PLUGIN_DIR,
            check=True,
            capture_output=True,
        )

    def test_zip_exists(self):
        self.assertTrue(ZIP_PATH.is_file())
        self.assertEqual(ZIP_PATH.name, 'plugin.Tab_Menu.zip')

    def test_listing_is_flat_plugin_root(self):
        names = subprocess.check_output(['unzip', '-Z', '-1', str(ZIP_PATH)], text=True).splitlines()
        names = [n.lstrip('./') for n in names]
        self.assertIn('install.inf', names)
        self.assertIn('__init__.py', names)
        self.assertIn('logic.py', names)
        self.assertIn('readme/readme.txt', names)
        self.assertIn('readme/history.txt', names)
        self.assertNotIn('cuda_tabmenu/__init__.py', names)
        self.assertFalse(any(n.startswith('cuda_tabmenu/') for n in names))
        self.assertFalse(any(n.startswith('anyascii/') for n in names))

    def test_listing_excludes_dev_files(self):
        names = subprocess.check_output(['unzip', '-Z', '-1', str(ZIP_PATH)], text=True).splitlines()
        names = [n.lstrip('./') for n in names]
        blob = '\n'.join(names)
        self.assertNotIn('release.json', blob)
        self.assertNotIn('addon-channel.json', blob)
        self.assertNotIn('pack.sh', blob)
        self.assertFalse(any(n == 'tests' or n.startswith('tests/') for n in names))
        self.assertFalse(any(n == 'dist' or n.startswith('dist/') for n in names))
        self.assertFalse(any('__pycache__' in n or n.endswith('.pyc') for n in names))

    def test_zip_has_no_ascii_tools(self):
        init = subprocess.check_output(['unzip', '-p', str(ZIP_PATH), '__init__.py'], text=True)
        inf = subprocess.check_output(['unzip', '-p', str(ZIP_PATH), 'install.inf'], text=True)
        self.assertNotIn('anyascii', init)
        self.assertNotIn('on_change_slow', init)
        self.assertNotIn('on_change_slow', inf)
        self.assertNotIn('on_init_plugins_menu', inf)
        self.assertNotIn('cuda_tabmenu_search', init)
        self.assertNotIn('Alt+F3', inf)
        self.assertIn('on_tab_menu', inf)
        self.assertIn('cmd_FileExportHtml', init)


class VersionSyncTests(unittest.TestCase):
    def test_install_inf_matches_init_and_logic(self):
        inf_ver = _version_from(PLUGIN_DIR / 'install.inf', 'version=')
        init_ver = _version_from(PLUGIN_DIR / '__init__.py', '__version__')
        logic_ver = _version_from(PLUGIN_DIR / 'logic.py', '__version__')
        self.assertEqual(inf_ver, '0.7.2')
        self.assertEqual(inf_ver, init_ver)
        self.assertEqual(inf_ver, logic_ver)
        self.assertGreater(inf_ver, '0.6.3')

    def test_subdir_matches_module_and_channel(self):
        inf = (PLUGIN_DIR / 'install.inf').read_text(encoding='utf-8')
        subdir = next(line.split('=', 1)[1].strip() for line in inf.splitlines() if line.startswith('subdir='))
        self.assertEqual(subdir, 'cuda_tabmenu')
        channel = (PLUGIN_DIR / 'addon-channel.json').read_text(encoding='utf-8')
        self.assertIn('"module": "cuda_tabmenu"', channel)
        release = (PLUGIN_DIR / 'release.json').read_text(encoding='utf-8')
        self.assertIn('plugin.Tab_Menu.zip', release)

    def test_history_starts_with_version_and_mentions_split(self):
        history = (PLUGIN_DIR / 'readme' / 'history.txt').read_text(encoding='utf-8')
        self.assertTrue(history.startswith('0.7.2 '))
        self.assertIn('ASCII Tools', history)
        self.assertIn('cuda-asciitools', history)

    def test_source_does_not_duplicate_stock_copy_commands(self):
        init = (PLUGIN_DIR / '__init__.py').read_text(encoding='utf-8')
        self.assertNotIn('Copy full filepath', init)
        self.assertNotIn('cmd_CopyFilename', init)
        # String id 'tab' rebuilds the stock popup. It may be resolved once.
        self.assertEqual(init.count("menu_proc('tab'"), 1)


if __name__ == '__main__':
    unittest.main()
