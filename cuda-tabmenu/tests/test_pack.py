import subprocess
import unittest
from pathlib import Path


PLUGIN_DIR = Path(__file__).resolve().parents[1]
ZIP_PATH = PLUGIN_DIR / 'dist' / 'plugin.Tab_Menu.zip'


class PackScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(['bash', str(PLUGIN_DIR / 'pack.sh')], cwd=PLUGIN_DIR, check=True, capture_output=True)

    def test_zip_exists(self):
        self.assertTrue(ZIP_PATH.is_file())

    def test_listing_has_plugin_files(self):
        names = subprocess.check_output(['unzip', '-Z', '-1', str(ZIP_PATH)], text=True).splitlines()
        names = [n.lstrip('./') for n in names]
        self.assertIn('install.inf', names)
        self.assertIn('__init__.py', names)
        self.assertIn('logic.py', names)
        self.assertIn('anyascii/__init__.py', names)
        self.assertNotIn('cuda_tabmenu/__init__.py', names)

    def test_listing_excludes_dev_files(self):
        listing = subprocess.check_output(['unzip', '-l', str(ZIP_PATH)], text=True)
        self.assertNotIn('release.json', listing)
        self.assertNotIn('addon-channel.json', listing)
        self.assertNotIn('/tests/', listing)
        self.assertNotIn('pack.sh', listing)


class VersionSyncTests(unittest.TestCase):
    def test_install_inf_matches_init(self):
        inf = (PLUGIN_DIR / 'install.inf').read_text(encoding='utf-8')
        init = (PLUGIN_DIR / '__init__.py').read_text(encoding='utf-8')
        inf_ver = next(line.split('=', 1)[1].strip() for line in inf.splitlines() if line.startswith('version='))
        init_ver = next(
            line.split('=', 1)[1].strip().strip('\'"')
            for line in init.splitlines()
            if line.startswith('__version__')
        )
        self.assertEqual(inf_ver, init_ver)


if __name__ == '__main__':
    unittest.main()
