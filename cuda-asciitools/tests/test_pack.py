import subprocess
import unittest
from pathlib import Path


PLUGIN_DIR = Path(__file__).resolve().parents[1]
ZIP_PATH = PLUGIN_DIR / 'dist' / 'plugin.ASCII_Tools.zip'


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
        self.assertEqual(ZIP_PATH.name, 'plugin.ASCII_Tools.zip')

    def test_listing_is_flat_plugin_root(self):
        names = subprocess.check_output(['unzip', '-Z', '-1', str(ZIP_PATH)], text=True).splitlines()
        names = [n.lstrip('./') for n in names]
        self.assertIn('install.inf', names)
        self.assertIn('__init__.py', names)
        self.assertIn('logic.py', names)
        self.assertIn('readme/readme.txt', names)
        self.assertIn('readme/history.txt', names)
        self.assertIn('anyascii/__init__.py', names)
        self.assertIn('anyascii/LICENSE', names)
        self.assertTrue(any(n.startswith('anyascii/_data/') for n in names))
        self.assertNotIn('cuda_asciitools/__init__.py', names)
        self.assertFalse(any(n.startswith('cuda_asciitools/') for n in names))
        self.assertFalse(any(n.startswith('cuda_tabmenu/') for n in names))

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

    def test_zip_has_no_tab_menu_hooks(self):
        init = subprocess.check_output(['unzip', '-p', str(ZIP_PATH), '__init__.py'], text=True)
        inf = subprocess.check_output(['unzip', '-p', str(ZIP_PATH), 'install.inf'], text=True)
        self.assertNotIn('on_tab_menu', init)
        self.assertNotIn('on_tab_menu', inf)
        self.assertNotIn('cuda_tabmenu_search', init)
        self.assertIn('cuda_asciitools_search', init)
        self.assertNotIn('anyascii', inf)


class VersionSyncTests(unittest.TestCase):
    def test_install_inf_matches_init_and_logic(self):
        inf_ver = _version_from(PLUGIN_DIR / 'install.inf', 'version=')
        init_ver = _version_from(PLUGIN_DIR / '__init__.py', '__version__')
        logic_ver = _version_from(PLUGIN_DIR / 'logic.py', '__version__')
        self.assertEqual(inf_ver, '0.1.0')
        self.assertEqual(inf_ver, init_ver)
        self.assertEqual(inf_ver, logic_ver)

    def test_subdir_matches_module_and_channel(self):
        inf = (PLUGIN_DIR / 'install.inf').read_text(encoding='utf-8')
        subdir = next(line.split('=', 1)[1].strip() for line in inf.splitlines() if line.startswith('subdir='))
        self.assertEqual(subdir, 'cuda_asciitools')
        channel = (PLUGIN_DIR / 'addon-channel.json').read_text(encoding='utf-8')
        self.assertIn('"module": "cuda_asciitools"', channel)
        release = (PLUGIN_DIR / 'release.json').read_text(encoding='utf-8')
        self.assertIn('plugin.ASCII_Tools.zip', release)

    def test_history_starts_with_version(self):
        history = (PLUGIN_DIR / 'readme' / 'history.txt').read_text(encoding='utf-8')
        self.assertTrue(history.startswith('0.1.0 '))

    def test_search_tag_is_not_the_old_tab_menu_tag(self):
        init = (PLUGIN_DIR / '__init__.py').read_text(encoding='utf-8')
        self.assertIn("SEARCH_MENU_TAG = 'cuda_asciitools_search'", init)
        self.assertNotIn('cuda_tabmenu_search', init)
        inf = (PLUGIN_DIR / 'install.inf').read_text(encoding='utf-8')
        self.assertIn('hotkey=Alt+F3', inf)
        self.assertIn('hotkey=Alt+Shift+F3', inf)
        self.assertIn('on_change_slow', inf)
        self.assertIn('on_init_plugins_menu', inf)


if __name__ == '__main__':
    unittest.main()
