import unittest
import time

from logic import (
    config_with_hints,
    CONFIG_HINTS,
    DEFAULT_CONFIG,
    merge_config,
    interval_elapsed,
    needs_update,
    select_outdated,
    format_result_summary,
    allowed_kinds,
    PREINST,
)


class TestMergeConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = merge_config(None)
        self.assertEqual(cfg['interval_hours'], 12)
        self.assertTrue(cfg['enabled'])

    def test_clamp(self):
        cfg = merge_config({'interval_hours': 0.01, 'poll_minutes': 0})
        self.assertGreaterEqual(cfg['interval_hours'], 0.25)
        self.assertGreaterEqual(cfg['poll_minutes'], 1)


class TestInterval(unittest.TestCase):
    def test_never_checked(self):
        self.assertTrue(interval_elapsed(0, 12, now=1000))

    def test_not_elapsed(self):
        now = 1_000_000
        last = now - 3600  # 1 hour ago
        self.assertFalse(interval_elapsed(last, 12, now=now))

    def test_elapsed(self):
        now = 1_000_000
        last = now - 13 * 3600
        self.assertTrue(interval_elapsed(last, 12, now=now))


class TestNeedsUpdate(unittest.TestCase):
    def test_preinst(self):
        self.assertFalse(needs_update(PREINST, '9.9'))

    def test_unknown_local(self):
        self.assertTrue(needs_update('?', '1.0'))
        self.assertTrue(needs_update('', '1.0'))

    def test_compare(self):
        self.assertTrue(needs_update('0.1.0', '0.2.0'))
        self.assertFalse(needs_update('0.2.0', '0.2.0'))
        self.assertFalse(needs_update('0.3.0', '0.2.0'))


class TestSelect(unittest.TestCase):
    def test_select_plugin(self):
        remote = [
            {'kind': 'plugin', 'name': 'Foo', 'module': 'cuda_foo', 'url': 'http://x/plugin.Foo.zip', 'v': '2.0'},
            {'kind': 'plugin', 'name': 'Bar', 'module': 'cuda_bar', 'url': 'http://x/plugin.Bar.zip', 'v': '1.0'},
        ]
        versions = {'plugin.Foo.zip': '1.0', 'plugin.Bar.zip': '1.0'}
        out = select_outdated(
            remote,
            ['cuda_foo', 'cuda_bar'],
            [],
            lambda url: versions.get(url.rsplit('/', 1)[-1], ''),
            {'plugin'},
        )
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]['module'], 'cuda_foo')


class TestSummary(unittest.TestCase):
    def test_none(self):
        self.assertEqual(format_result_summary([], [], [], []), 'No addon updates needed')

    def test_mix(self):
        s = format_result_summary(['A'], ['B'], ['C'], [])
        self.assertIn('updated: A', s)
        self.assertIn('failed: B', s)
        self.assertIn('git pull: C', s)


class TestKinds(unittest.TestCase):
    def test_default_kinds(self):
        k = allowed_kinds(DEFAULT_CONFIG)
        self.assertIn('plugin', k)
        self.assertNotIn('lexer', k)


if __name__ == '__main__':
    unittest.main()


class TestHints(unittest.TestCase):
    def test_hints_written_and_ignored_on_load(self):
        raw = config_with_hints(merge_config(None))
        self.assertIn('enabled_Hint', raw)
        self.assertTrue(raw['enabled_Hint'])
        self.assertEqual(len(CONFIG_HINTS), len([k for k in raw if k.endswith('_Hint')]))
        cfg = merge_config(raw)
        self.assertNotIn('enabled_Hint', cfg)
        self.assertTrue(cfg['enabled'])
