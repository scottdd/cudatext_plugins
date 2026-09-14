import tempfile
import unittest
from pathlib import Path

from release_plugin import (
    notes_from_history,
    parse_github_slug,
    read_version_from_init,
    upsert_channel_entry,
    ReleaseError,
)


class ParseGithubSlugTests(unittest.TestCase):
    def test_ssh(self):
        self.assertEqual(
            parse_github_slug('git@github.com:scottdd/cudatext_plugins.git'),
            'scottdd/cudatext_plugins',
        )

    def test_https(self):
        self.assertEqual(
            parse_github_slug('https://github.com/scottdd/cudatext_plugins.git'),
            'scottdd/cudatext_plugins',
        )

    def test_https_without_git_suffix(self):
        self.assertEqual(
            parse_github_slug('https://github.com/scottdd/cudatext_plugins'),
            'scottdd/cudatext_plugins',
        )

    def test_bad_url(self):
        with self.assertRaises(ReleaseError):
            parse_github_slug('https://example.com/not-github')


class ChannelTests(unittest.TestCase):
    def test_insert_sorted(self):
        entries = upsert_channel_entry(
            [],
            module='cuda_tabmenu',
            desc='desc',
            version='0.6',
            url='https://example/plugin.zip',
        )
        self.assertEqual(entries[0]['v'], '0.6')
        self.assertEqual(entries[0]['module'], 'cuda_tabmenu')

    def test_update_existing(self):
        start = [{'url': 'old', 'desc': 'old', 'module': 'cuda_tabmenu', 'v': '0.5'}]
        entries = upsert_channel_entry(
            start,
            module='cuda_tabmenu',
            desc='new',
            version='0.6',
            url='https://example/new.zip',
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['v'], '0.6')
        self.assertEqual(entries[0]['url'], 'https://example/new.zip')


class HistoryNotesTests(unittest.TestCase):
    def test_first_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'history.txt'
            path.write_text('one\ntwo\nthree\n', encoding='utf-8')
            self.assertEqual(notes_from_history(path, max_lines=2), 'one\ntwo')

    def test_missing_file(self):
        self.assertEqual(notes_from_history(Path('/no/such/history.txt')), '')


class VersionReadTests(unittest.TestCase):
    def test_reads_dunder_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp)
            (plugin / '__init__.py').write_text("__version__ = '0.6'\n", encoding='utf-8')
            self.assertEqual(read_version_from_init(plugin), '0.6')


if __name__ == '__main__':
    unittest.main()
