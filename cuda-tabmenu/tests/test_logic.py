import os
import tempfile
import time
import unittest
from pathlib import Path

from logic import (
    FileOpError,
    available_attempts,
    clean_duplicate_basename,
    count_characters,
    count_words,
    encode_document,
    first_available,
    first_path,
    format_file_info,
    format_line_endings,
    format_size,
    format_status,
    format_timestamp,
    open_folder_attempts,
    path_to_file_uri,
    platform_from_suffix,
    prepare_destination,
    reveal_attempts,
    safe_copy_file,
    safe_delete_file,
    safe_write_bytes,
    suggest_duplicate_name,
    terminal_attempts,
)


class FormatSizeTests(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(format_size(0), '0 B')

    def test_bytes(self):
        self.assertEqual(format_size(512), '512.0 B')

    def test_kilobytes(self):
        self.assertEqual(format_size(2048), '2.0 kB')

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            format_size(-1)


class CountTests(unittest.TestCase):
    def test_words_empty(self):
        self.assertEqual(count_words(''), 0)
        self.assertEqual(count_words(None), 0)

    def test_words_simple(self):
        self.assertEqual(count_words('hello world'), 2)

    def test_words_extra_space(self):
        self.assertEqual(count_words('  one   two\nthree  '), 3)

    def test_characters_include_line_breaks(self):
        self.assertEqual(count_characters('ab\n'), 3)
        self.assertEqual(count_characters(''), 0)
        self.assertEqual(count_characters('é'), 1)


class StatusTests(unittest.TestCase):
    def test_status_matrix(self):
        self.assertEqual(format_status(False, False, False), 'unsaved')
        self.assertEqual(format_status(False, True, True), 'unsaved, read-only')
        self.assertEqual(format_status(True, True, False), 'modified')
        self.assertEqual(format_status(True, True, True), 'modified, read-only')
        self.assertEqual(format_status(True, False, False), 'saved')
        self.assertEqual(format_status(True, False, True), 'saved, read-only')

    def test_line_endings(self):
        self.assertEqual(format_line_endings('lf'), 'LF (Unix)')
        self.assertEqual(format_line_endings('crlf'), 'CRLF (Windows)')
        self.assertEqual(format_line_endings('cr'), 'CR (classic Mac)')
        self.assertEqual(format_line_endings(''), '(none)')
        self.assertEqual(format_line_endings(None), '(none)')
        self.assertEqual(format_line_endings('nel'), 'nel')

    def test_timestamp_uses_local_time(self):
        stamp = 1700000000
        expected = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stamp))
        self.assertEqual(format_timestamp(stamp), expected)
        self.assertEqual(format_timestamp(None), '(none)')

    def test_file_info_omits_missing_and_aligns(self):
        text = format_file_info({
            'path': '/tmp/a.txt',
            'filename': 'a.txt',
            'status': 'modified, read-only',
            'encoding': 'utf-8',
            'line_endings': 'LF (Unix)',
            'lexer': 'Python',
            'size_disk': '4.0 B',
            'size_memory': None,
            'lines': '2',
            'words': '3',
            'characters': '10',
            'modified': '2026-11-23 12:00:00',
        })
        self.assertIn('Full path', text)
        self.assertIn('/tmp/a.txt', text)
        self.assertIn('modified, read-only', text)
        self.assertIn('LF (Unix)', text)
        self.assertNotIn('Size in memory', text)
        self.assertIn('Last modified', text)
        lines = text.splitlines()
        colon_at = {line.index(':') for line in lines}
        self.assertEqual(len(colon_at), 1)


class DuplicateNameTests(unittest.TestCase):
    def test_first_choice_is_stem_copy(self):
        self.assertEqual(suggest_duplicate_name('notes.txt', lambda name: False), 'notes_copy.txt')

    def test_collision_increments(self):
        used = {'notes_copy.txt', 'notes_copy2.txt'}
        self.assertEqual(
            suggest_duplicate_name('notes.txt', lambda name: name in used),
            'notes_copy3.txt',
        )

    def test_hidden_and_multi_dot(self):
        self.assertEqual(suggest_duplicate_name('.gitignore', lambda name: False), '.gitignore_copy')
        self.assertEqual(suggest_duplicate_name('a.tar.gz', lambda name: False), 'a.tar_copy.gz')

    def test_basename_rejects_paths(self):
        self.assertEqual(clean_duplicate_basename('  notes.txt  '), 'notes.txt')
        with self.assertRaises(FileOpError):
            clean_duplicate_basename('')
        with self.assertRaises(FileOpError):
            clean_duplicate_basename('..')
        with self.assertRaises(FileOpError):
            clean_duplicate_basename('dir/notes.txt')
        with self.assertRaises(FileOpError):
            clean_duplicate_basename('dir\\notes.txt')


class FileOpTests(unittest.TestCase):
    def test_write_copy_and_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'src.txt')
            dest = os.path.join(tmp, 'dest.txt')
            with open(src, 'wb') as handle:
                handle.write(b'abc')
            safe_copy_file(src, dest)
            self.assertEqual(Path(dest).read_bytes(), b'abc')
            with self.assertRaises(FileOpError):
                safe_copy_file(src, src)
            with self.assertRaises(FileOpError):
                safe_write_bytes(dest, b'nope', overwrite=False)
            safe_write_bytes(dest, b'yes', overwrite=True)
            self.assertEqual(Path(dest).read_bytes(), b'yes')
            saved = Path(src).read_bytes()
            safe_delete_file(dest)
            self.assertFalse(os.path.exists(dest))
            self.assertEqual(Path(src).read_bytes(), saved)

    def test_refuses_directories_and_missing_parents(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileOpError):
                safe_delete_file(tmp)
            with self.assertRaises(FileOpError):
                prepare_destination(os.path.join(tmp, 'missing', 'a.txt'))
            with self.assertRaises(FileOpError):
                prepare_destination(tmp)
            with self.assertRaises(FileOpError):
                safe_delete_file(os.path.join(tmp, 'nope.txt'))
            with self.assertRaises(FileOpError):
                safe_write_bytes(os.path.join(tmp, 'a.txt'), 'not-bytes')

    def test_delete_symlink_to_file_keeps_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, 'target.txt')
            link = os.path.join(tmp, 'link.txt')
            with open(target, 'wb') as handle:
                handle.write(b'data')
            os.symlink(target, link)
            safe_delete_file(link)
            self.assertFalse(os.path.lexists(link))
            self.assertEqual(Path(target).read_bytes(), b'data')

    def test_refuses_symlink_to_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = os.path.join(tmp, 'folder')
            os.mkdir(folder)
            link = os.path.join(tmp, 'linkdir')
            os.symlink(folder, link)
            with self.assertRaises(FileOpError):
                safe_delete_file(link)
            self.assertTrue(os.path.isdir(folder))
            self.assertTrue(os.path.islink(link))

    def test_first_path(self):
        self.assertEqual(first_path(None), '')
        self.assertEqual(first_path('a'), 'a')
        self.assertEqual(first_path(['a', 'b']), 'a')
        self.assertEqual(first_path([]), '')


class EncodingTests(unittest.TestCase):
    def test_utf8_bom_and_crlf(self):
        data = encode_document('é\n', 'utf8_bom', newline='crlf')
        self.assertTrue(data.startswith(b'\xef\xbb\xbf'))
        self.assertEqual(data[3:], 'é\r\n'.encode('utf-8'))

    def test_does_not_double_bom(self):
        data = encode_document('\ufeffA', 'utf-8_bom', newline='keep')
        self.assertEqual(data, b'\xef\xbb\xbfA')

    def test_cp1252_and_utf16(self):
        self.assertEqual(encode_document('é', 'cp1252', newline='keep'), b'\xe9')
        data = encode_document('A', 'utf16le_bom', newline='keep')
        self.assertEqual(data, b'\xff\xfeA\x00')

    def test_keep_and_cr(self):
        self.assertEqual(encode_document('a\r\nb', 'utf-8', newline='lf'), b'a\nb')
        self.assertEqual(encode_document('a\nb', 'utf-8', newline='cr'), b'a\rb')

    def test_empty_encoding_is_utf8(self):
        self.assertEqual(encode_document('A', '', newline='keep'), b'A')

    def test_unknown_encoding_and_newline(self):
        with self.assertRaises(FileOpError):
            encode_document('A', 'not-a-real-encoding')
        with self.assertRaises(FileOpError):
            encode_document('A', 'utf-8', newline='nel')
        with self.assertRaises(FileOpError):
            encode_document('é', 'ascii', newline='keep')


class PlatformCommandTests(unittest.TestCase):
    def test_suffix_map(self):
        self.assertEqual(platform_from_suffix(''), 'windows')
        self.assertEqual(platform_from_suffix(None), 'windows')
        self.assertEqual(platform_from_suffix('__mac'), 'macos')
        self.assertEqual(platform_from_suffix('__haiku'), 'haiku')
        self.assertEqual(platform_from_suffix('__linux'), 'linux')

    def test_file_uri_quotes_spaces(self):
        self.assertEqual(path_to_file_uri('/tmp/my file.txt'), 'file:///tmp/my%20file.txt')

    def test_reveal_commands(self):
        windows = reveal_attempts('windows', r'C:\docs\a b.txt')
        self.assertEqual(windows[0]['argv'][0], 'explorer')
        self.assertTrue(windows[0]['argv'][1].startswith('/select,'))
        self.assertIn('a b.txt', windows[0]['argv'][1])

        mac = reveal_attempts('macos', '/tmp/a.txt')
        self.assertEqual(mac[0]['argv'], ['open', '-R', '/tmp/a.txt'])

        linux = reveal_attempts('linux', '/tmp/my file.txt')
        joined = ' '.join(linux[0]['argv'])
        self.assertIn('org.freedesktop.FileManager1.ShowItems', joined)
        self.assertIn('file:///tmp/my%20file.txt', joined)
        self.assertEqual(linux[0]['check'], 'dbus-send')
        self.assertTrue(linux[0]['wait'])
        self.assertEqual(linux[1]['check'], 'gdbus')
        self.assertEqual(linux[-1]['argv'], ['xdg-open', '/tmp'])
        self.assertFalse(linux[-1]['wait'])
        self.assertEqual(reveal_attempts('haiku', '/tmp/a.txt'), [])

    def test_open_folder_commands(self):
        self.assertEqual(open_folder_attempts('linux', '/tmp')[0]['argv'], ['xdg-open', '/tmp'])
        self.assertEqual(open_folder_attempts('macos', '/tmp')[0]['argv'], ['open', '/tmp'])
        self.assertEqual(open_folder_attempts('windows', '/tmp')[0]['argv'][0], 'explorer')
        self.assertEqual(open_folder_attempts('haiku', '/tmp')[0]['argv'][0], 'open')

    def test_terminal_picks_first_available(self):
        linux = terminal_attempts('linux', '/tmp/proj')
        checks = [item.get('check') for item in linux]
        self.assertLess(checks.index('gnome-terminal'), checks.index('x-terminal-emulator'))
        chosen = first_available(linux, lambda name: name == 'gnome-terminal')
        self.assertEqual(chosen['argv'][0], 'gnome-terminal')
        self.assertEqual(chosen['argv'][1:], ['--working-directory', '/tmp/proj'])
        self.assertEqual(chosen['cwd'], '/tmp/proj')

        windows = terminal_attempts('windows', r'C:\work')
        preferred = first_available(windows, lambda name: name in ('wt.exe', 'wt'))
        self.assertEqual(preferred['argv'][0], 'wt.exe')
        self.assertEqual(preferred['argv'][1], '-d')
        fallback = first_available(windows, lambda name: False)
        self.assertEqual(fallback['argv'][0], 'cmd.exe')
        self.assertIn('/K', fallback['argv'])

        mac = terminal_attempts('macos', '/tmp')
        self.assertEqual(mac[0]['argv'][:3], ['open', '-a', 'Terminal'])

        runnable = available_attempts(linux, lambda name: name in ('kitty', 'xterm'))
        self.assertEqual([item['check'] for item in runnable], ['kitty', 'xterm'])
        self.assertEqual(terminal_attempts('haiku', '/tmp'), [])


if __name__ == '__main__':
    unittest.main()
