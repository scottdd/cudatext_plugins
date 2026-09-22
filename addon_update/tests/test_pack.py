import subprocess
import unittest
from pathlib import Path


PLUGIN_DIR = Path(__file__).resolve().parents[1]
ZIP_PATH = PLUGIN_DIR / 'dist' / 'plugin.Addon_Update.zip'


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

    def test_listing_is_flat_plugin_root(self):
        names = subprocess.check_output(['unzip', '-Z', '-1', str(ZIP_PATH)], text=True).splitlines()
        names = [n.lstrip('./') for n in names]
        self.assertIn('install.inf', names)
        self.assertIn('__init__.py', names)
        self.assertIn('logic.py', names)
        self.assertIn('readme/readme.txt', names)
        # Must NOT nest under module folder (tabmenu flat-zip lesson)
        self.assertNotIn('cuda_addon_update/__init__.py', names)
        self.assertFalse(any(n.startswith('cuda_addon_update/') for n in names))

    def test_listing_excludes_dev_files(self):
        listing = subprocess.check_output(['unzip', '-l', str(ZIP_PATH)], text=True)
        self.assertNotIn('release.json', listing)
        self.assertNotIn('addon-channel.json', listing)
        self.assertNotIn('/tests/', listing)
        self.assertNotIn('pack.sh', listing)

    def test_channel_url_kind_name_pattern(self):
        # Addon Manager parses kind/name from .../(\w+)\.(.+?)\.zip
        self.assertEqual(ZIP_PATH.name, 'plugin.Addon_Update.zip')
        channel = (PLUGIN_DIR / 'addon-channel.json').read_text(encoding='utf-8')
        self.assertIn('plugin.Addon_Update.zip', channel)
        self.assertIn('"module": "cuda_addon_update"', channel)


class VersionSyncTests(unittest.TestCase):
    def test_install_inf_matches_init_and_logic(self):
        inf = (PLUGIN_DIR / 'install.inf').read_text(encoding='utf-8')
        init = (PLUGIN_DIR / '__init__.py').read_text(encoding='utf-8')
        logic = (PLUGIN_DIR / 'logic.py').read_text(encoding='utf-8')
        inf_ver = next(line.split('=', 1)[1].strip() for line in inf.splitlines() if line.startswith('version='))
        init_ver = next(
            line.split('=', 1)[1].strip().strip('\'"')
            for line in init.splitlines()
            if line.startswith('__version__')
        )
        logic_ver = next(
            line.split('=', 1)[1].strip().strip('\'"')
            for line in logic.splitlines()
            if line.startswith('__version__')
        )
        self.assertEqual(inf_ver, init_ver)
        self.assertEqual(inf_ver, logic_ver)

    def test_subdir_matches_module_channel(self):
        inf = (PLUGIN_DIR / 'install.inf').read_text(encoding='utf-8')
        subdir = next(line.split('=', 1)[1].strip() for line in inf.splitlines() if line.startswith('subdir='))
        self.assertEqual(subdir, 'cuda_addon_update')
        channel = (PLUGIN_DIR / 'addon-channel.json').read_text(encoding='utf-8')
        self.assertIn(f'"module": "{subdir}"', channel)


if __name__ == '__main__':
    unittest.main()
