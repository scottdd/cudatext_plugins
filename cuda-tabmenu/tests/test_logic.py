import os
import tempfile
import time
import unittest
from pathlib import Path

from logic import (
    FileOpError,
    available_attempts,
    bgr_from_rgb,
    KEY_C,
    KEY_ESCAPE,
    KEY_RETURN,
    build_file_info_dialog,
    button_ex_label,
    clean_duplicate_basename,
    file_info_key_action,
    coerce_tcolor,
    count_characters,
    count_words,
    encode_document,
    file_info_badges,
    file_info_folder,
    file_info_sections,
    file_info_status_colors,
    first_available,
    first_path,
    format_file_info,
    format_line_endings,
    format_size,
    format_status,
    format_timestamp,
    html_color_to_tcolor,
    is_dark_color,
    mix_tcolor,
    open_folder_attempts,
    parent_folder,
    parse_file_status,
    path_to_file_uri,
    platform_from_suffix,
    prepare_destination,
    relative_luminance,
    resolve_ui_palette,
    reveal_attempts,
    rgb_from_bgr,
    safe_copy_file,
    safe_delete_file,
    safe_write_bytes,
    suggest_duplicate_name,
    terminal_attempts,
)

INIT_PY = Path(__file__).resolve().parents[1] / '__init__.py'


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


def _theme_entry(html):
    return {'desc': 'test', 'color': html_color_to_tcolor(html)}


def dark_theme():
    return {
        'ListBg': _theme_entry('#202020'),
        'ListFont': _theme_entry('#E8E8E8'),
    }


def light_theme():
    return {
        'ListBg': _theme_entry('#F7F7F7'),
        'ListFont': _theme_entry('#202020'),
    }


class TColorTests(unittest.TestCase):
    def test_bgr_packing_swaps_red_and_blue(self):
        self.assertEqual(bgr_from_rgb(255, 0, 0), 0x0000FF)
        self.assertEqual(bgr_from_rgb(0, 255, 0), 0x00FF00)
        self.assertEqual(bgr_from_rgb(0, 0, 255), 0xFF0000)
        self.assertEqual(rgb_from_bgr(0x0000FF), (255, 0, 0))
        self.assertEqual(rgb_from_bgr(0x00FF00), (0, 255, 0))
        self.assertEqual(rgb_from_bgr(0xFF0000), (0, 0, 255))

    def test_green_is_unchanged_and_amber_is_not_blue(self):
        # A missed swap leaves green green. Amber #E0A100 stored as 0xE0A100
        # is blue in a Lazarus TColor.
        self.assertEqual(html_color_to_tcolor('#00FF00'), 0x00FF00)
        self.assertEqual(html_color_to_tcolor('#0F0'), 0x00FF00)
        amber = html_color_to_tcolor('#E0A100')
        self.assertEqual(amber, 0x00A1E0)
        self.assertNotEqual(amber, 0xE0A100)
        self.assertEqual(rgb_from_bgr(amber), (0xE0, 0xA1, 0x00))
        mistaken = rgb_from_bgr(0xE0A100)
        self.assertGreater(mistaken[2], mistaken[0])

    def test_roundtrip_samples(self):
        samples = (
            '#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF',
            '#E0A100', '#123456', '#0F0', '#39C', '#1A1A2E',
        )
        for html in samples:
            color = html_color_to_tcolor(html)
            self.assertGreaterEqual(color, 0)
            self.assertLessEqual(color, 0xFFFFFF)
            red, green, blue = rgb_from_bgr(color)
            self.assertEqual(bgr_from_rgb(red, green, blue), color)
            self.assertEqual(rgb_from_bgr(bgr_from_rgb(red, green, blue)), (red, green, blue))

    def test_html_rejects_bad_input(self):
        for value in ('', '#', '#12', '#12345', '#GGGGGG', 'not-a-color', '#E0A100FF'):
            with self.assertRaises(ValueError):
                html_color_to_tcolor(value)

    def test_coerce_passes_tcolor_through_and_drops_sentinels(self):
        amber = html_color_to_tcolor('#E0A100')
        self.assertEqual(coerce_tcolor(amber), amber)
        self.assertEqual(coerce_tcolor({'color': amber, 'desc': 'editor, BG'}), amber)
        self.assertEqual(coerce_tcolor({'color': '#E0A100'}), amber)
        self.assertEqual(coerce_tcolor('#1A1A2E'), html_color_to_tcolor('#1A1A2E'))
        self.assertIsNone(coerce_tcolor(0x1FFFFFFF))
        self.assertIsNone(coerce_tcolor(0x20000000))
        self.assertIsNone(coerce_tcolor(-2147483648))
        self.assertIsNone(coerce_tcolor(True))
        self.assertIsNone(coerce_tcolor(False))
        self.assertIsNone(coerce_tcolor(None))
        self.assertIsNone(coerce_tcolor('nope'))
        self.assertIsNone(coerce_tcolor({'desc': 'missing color'}))

    def test_luminance_and_mix(self):
        black = html_color_to_tcolor('#000000')
        white = html_color_to_tcolor('#FFFFFF')
        self.assertAlmostEqual(relative_luminance(black), 0.0)
        self.assertAlmostEqual(relative_luminance(white), 1.0)
        self.assertTrue(is_dark_color(html_color_to_tcolor('#202020')))
        self.assertTrue(is_dark_color(html_color_to_tcolor('#1A1A2E')))
        self.assertFalse(is_dark_color(html_color_to_tcolor('#E4E4E4')))
        self.assertFalse(is_dark_color(html_color_to_tcolor('#F7F7F7')))
        self.assertEqual(mix_tcolor(black, white, 0), black)
        self.assertEqual(mix_tcolor(black, white, 1), white)
        self.assertEqual(rgb_from_bgr(mix_tcolor(black, white, 0.5)), (128, 128, 128))


class PaletteTests(unittest.TestCase):
    def test_dark_and_light_themes_keep_bgr_background(self):
        dark = resolve_ui_palette(dark_theme())
        light = resolve_ui_palette(light_theme())
        self.assertTrue(dark['dark'])
        self.assertFalse(light['dark'])
        self.assertEqual(dark['background'], html_color_to_tcolor('#202020'))
        self.assertEqual(light['background'], html_color_to_tcolor('#F7F7F7'))
        self.assertGreater(relative_luminance(dark['text']), relative_luminance(dark['background']))
        self.assertLess(relative_luminance(light['text']), relative_luminance(light['background']))
        for palette in (dark, light):
            self.assertGreater(
                relative_luminance(palette['muted']) if palette['dark'] else relative_luminance(palette['background']),
                relative_luminance(palette['background']) if palette['dark'] else relative_luminance(palette['muted']),
            )
            bg = relative_luminance(palette['background'])
            text = relative_luminance(palette['text'])
            muted = relative_luminance(palette['muted'])
            divider = relative_luminance(palette['divider'])
            low = min(bg, text)
            high = max(bg, text)
            self.assertLess(low, divider)
            self.assertGreater(high, divider)
            self.assertLess(low, muted)
            self.assertGreater(high, muted)

    def test_asymmetric_theme_color_is_not_swapped_again(self):
        color = html_color_to_tcolor('#1A1A2E')
        palette = resolve_ui_palette({'EdTextBg': {'color': color, 'desc': 'editor, BG'}})
        self.assertEqual(palette['background'], color)
        self.assertEqual(rgb_from_bgr(palette['background']), (0x1A, 0x1A, 0x2E))
        self.assertTrue(palette['dark'])

    def test_empty_partial_and_invalid_themes(self):
        for theme in (None, {}, [], 'nope', {'ListBg': {'desc': 'x'}}):
            palette = resolve_ui_palette(theme)
            self.assertFalse(palette['dark'])
            self.assertGreaterEqual(palette['background'], 0)
            self.assertLessEqual(palette['background'], 0xFFFFFF)
            self.assertGreater(relative_luminance(palette['background']), relative_luminance(palette['text']))

        skipped = resolve_ui_palette({
            'ListBg': {'color': 0x1FFFFFFF},
            'TreeBg': {'color': ''},
            'EdTextBg': '#202020',
        })
        self.assertEqual(skipped['background'], html_color_to_tcolor('#202020'))
        self.assertTrue(skipped['dark'])

        string_theme = resolve_ui_palette({'ListBg': '#303030', 'ButtonFont': '#EEEEEE'})
        self.assertEqual(string_theme['background'], html_color_to_tcolor('#303030'))
        self.assertEqual(string_theme['text'], html_color_to_tcolor('#EEEEEE'))
        self.assertTrue(string_theme['dark'])

    def test_low_contrast_text_is_replaced(self):
        palette = resolve_ui_palette({
            'ListBg': _theme_entry('#202020'),
            'ListFont': _theme_entry('#242424'),
        })
        self.assertGreater(relative_luminance(palette['text']), 0.5)
        self.assertTrue(palette['dark'])

    def test_status_colors_are_bgr_and_amber_is_not_blue(self):
        for dark in (True, False):
            saved = file_info_status_colors(dark, 'saved')
            modified = file_info_status_colors(dark, 'modified')
            unsaved = file_info_status_colors(dark, 'unsaved')
            readonly = file_info_status_colors(dark, 'readonly')
            for colors in (saved, modified, unsaved, readonly):
                for key in ('fill', 'text', 'border', 'accent'):
                    self.assertGreaterEqual(colors[key], 0)
                    self.assertLessEqual(colors[key], 0xFFFFFF)
            for key in ('fill', 'text', 'accent'):
                red, green, blue = rgb_from_bgr(saved[key])
                self.assertGreater(green, red)
                self.assertGreater(green, blue)
                red, green, blue = rgb_from_bgr(modified[key])
                self.assertGreater(red, green)
                self.assertGreater(green, blue)
                if key != 'fill':
                    self.assertGreater(red - blue, 40)
            # The mistaken RGB integer for the dark amber accent is blue.
            self.assertNotEqual(modified['accent'], 0xE6A23C if dark else 0xC4841D)
            self.assertEqual(
                modified['accent'],
                html_color_to_tcolor('#E6A23C' if dark else '#C4841D'),
            )
            for colors in (unsaved, readonly):
                red, green, blue = rgb_from_bgr(colors['fill'])
                self.assertLess(max(red, green, blue) - min(red, green, blue), 30)

        with self.assertRaises(ValueError):
            file_info_status_colors(True, 'missing')


class FileInfoModelTests(unittest.TestCase):
    def test_status_badges(self):
        self.assertEqual(parse_file_status('saved'), ('saved', False))
        self.assertEqual(parse_file_status('modified, read-only'), ('modified', True))
        self.assertEqual(parse_file_status('unsaved, read-only'), ('unsaved', True))
        self.assertEqual(
            file_info_badges({'status': 'saved'}),
            [{'kind': 'saved', 'label': 'Saved'}],
        )
        self.assertEqual(
            file_info_badges({'status': 'unsaved, read-only'}),
            [
                {'kind': 'unsaved', 'label': 'Unsaved'},
                {'kind': 'readonly', 'label': 'Read-only'},
            ],
        )

    def test_parent_folder_and_unsaved_label(self):
        self.assertEqual(parent_folder('/home/scott/projects/a.txt'), '/home/scott/projects')
        self.assertEqual(parent_folder('/a.txt'), '/')
        self.assertEqual(parent_folder('a.txt'), '')
        self.assertEqual(parent_folder(r'C:\docs\a b.txt'), r'C:\docs')
        self.assertEqual(parent_folder('C:/docs/a.txt'), 'C:/docs')
        self.assertEqual(
            file_info_folder({'status': 'saved', 'path': '/home/scott/a.txt'}),
            '/home/scott',
        )
        self.assertEqual(
            file_info_folder({'status': 'unsaved', 'path': '(unsaved)'}),
            '(Unsaved)',
        )
        self.assertEqual(
            file_info_folder({'status': 'unsaved', 'path': '(non enregistre)'}, unsaved_label='(Unsaved)'),
            '(Unsaved)',
        )

    def test_sections_omit_optional_and_non_text_rows(self):
        saved = file_info_sections({
            'encoding': 'utf-8',
            'line_endings': 'LF (Unix)',
            'lexer': 'Python',
            'size_disk': '4.0 B',
            'size_memory': None,
            'modified': '2026-11-23 12:00:00',
            'lines': '2',
            'words': '3',
            'characters': '10',
        })
        self.assertEqual([item['key'] for item in saved], ['file', 'text'])
        self.assertEqual(
            [label for label, _value in saved[0]['rows']],
            ['Encoding', 'Line endings', 'Lexer', 'Size on disk', 'Last modified'],
        )
        self.assertEqual(
            [label for label, _value in saved[1]['rows']],
            ['Lines', 'Words', 'Characters'],
        )
        unsaved = file_info_sections({
            'encoding': 'utf-8',
            'line_endings': 'LF (Unix)',
            'lexer': '(none)',
            'size_memory': '4.0 B',
            'lines': '1',
            'words': '0',
            'characters': '0',
        })
        file_labels = [label for label, _value in unsaved[0]['rows']]
        self.assertIn('Size in memory', file_labels)
        self.assertNotIn('Size on disk', file_labels)
        self.assertNotIn('Last modified', file_labels)
        binary = file_info_sections({
            'encoding': 'binary',
            'line_endings': '(none)',
            'lexer': '(none)',
            'size_disk': '8.0 B',
            'modified': '2026-11-23 12:00:00',
        })
        self.assertEqual([item['key'] for item in binary], ['file'])


def _saved_info(**extra):
    info = {
        'path': '/home/scott/projects/cudatext_plugins/cuda-tabmenu/logic.py',
        'filename': 'logic.py',
        'status': 'saved',
        'encoding': 'utf-8',
        'line_endings': 'LF (Unix)',
        'lexer': 'Python',
        'size_disk': '12.0 kB',
        'modified': '2026-11-23 12:00:00',
        'lines': '450',
        'words': '1200',
        'characters': '9000',
    }
    info.update(extra)
    return info


def _control(spec, name):
    matches = [item for item in spec['controls'] if item['prop'].get('name') == name]
    if len(matches) != 1:
        raise AssertionError('%s found %d times' % (name, len(matches)))
    return matches[0]


def _row_labels(spec, key):
    labels = []
    index = 0
    while True:
        name = '%s_label_%d' % (key, index)
        matches = [item for item in spec['controls'] if item['prop'].get('name') == name]
        if not matches:
            return labels
        labels.append(matches[0]['prop']['cap'])
        index += 1


class FileInfoDialogTests(unittest.TestCase):
    def _assert_inside(self, spec):
        names = []
        for control in spec['controls']:
            prop = control['prop']
            names.append(prop['name'])
            self.assertGreaterEqual(prop['x'], 0)
            self.assertGreaterEqual(prop['y'], 0)
            self.assertGreater(prop['w'], 0)
            self.assertGreater(prop['h'], 0)
            self.assertLessEqual(prop['x'] + prop['w'], spec['width'])
            self.assertLessEqual(prop['y'] + prop['h'], spec['height'])
            for key in ('color', 'font_color', 'ex1', 'ex2', 'ex3'):
                if key not in prop or not isinstance(prop[key], int):
                    continue
                self.assertGreaterEqual(prop[key], 0)
                self.assertLessEqual(prop[key], 0xFFFFFF)
        self.assertEqual(len(names), len(set(names)))
        self.assertNotIn('memo', [item['type'] for item in spec['controls']])

    def test_copy_text_matches_format_file_info(self):
        info = _saved_info(status='modified, read-only', size_memory=None)
        spec = build_file_info_dialog(info, dark_theme())
        self.assertEqual(spec['copy_text'], format_file_info(info))
        self.assertNotIn('Size in memory', spec['copy_text'])
        self.assertIn('Size in memory (UTF-8)', format_file_info(_saved_info(
            status='modified',
            size_memory='1.0 kB',
        )))
        themed = build_file_info_dialog(info, light_theme())
        self.assertEqual(themed['copy_text'], spec['copy_text'])

    def test_saved_modified_unsaved_and_non_text_rows(self):
        saved = build_file_info_dialog(_saved_info(), light_theme())
        modified = build_file_info_dialog(_saved_info(status='modified', size_memory='1.0 kB'), light_theme())
        unsaved = build_file_info_dialog({
            'path': '(unsaved)',
            'filename': 'Untitled',
            'status': 'unsaved',
            'encoding': 'utf-8',
            'line_endings': 'LF (Unix)',
            'lexer': '(none)',
            'size_memory': '4.0 B',
            'lines': '1',
            'words': '0',
            'characters': '0',
        }, dark_theme())
        binary = build_file_info_dialog({
            'path': '/tmp/blob.bin',
            'filename': 'blob.bin',
            'status': 'saved',
            'encoding': 'binary',
            'line_endings': '(none)',
            'lexer': '(none)',
            'size_disk': '8.0 B',
            'modified': '2026-11-23 12:00:00',
        }, dark_theme())

        self.assertEqual(
            _row_labels(saved, 'file'),
            ['Encoding', 'Line endings', 'Lexer', 'Size on disk', 'Last modified'],
        )
        self.assertEqual(_row_labels(saved, 'text'), ['Lines', 'Words', 'Characters'])
        self.assertEqual(
            _row_labels(modified, 'file'),
            ['Encoding', 'Line endings', 'Lexer', 'Size on disk', 'Size in memory', 'Last modified'],
        )
        self.assertNotIn('Size in memory (UTF-8)', _row_labels(modified, 'file'))
        self.assertEqual(
            _row_labels(unsaved, 'file'),
            ['Encoding', 'Line endings', 'Lexer', 'Size in memory'],
        )
        self.assertEqual(_row_labels(binary, 'text'), [])
        self.assertNotIn('divider', [item['prop']['name'] for item in binary['controls']])
        self.assertIn('divider', [item['prop']['name'] for item in saved['controls']])

        row_delta = modified['height'] - saved['height']
        self.assertGreater(row_delta, 0)
        self.assertEqual(saved['height'] - unsaved['height'], row_delta)
        self.assertGreater(saved['height'] - binary['height'], 3 * row_delta)
        self.assertEqual(saved['width'], unsaved['width'])
        self.assertEqual(saved['width'], binary['width'])

        for spec in (saved, modified, unsaved, binary):
            self._assert_inside(spec)
            labels = [
                item for item in spec['controls']
                if item['prop']['name'].endswith('_label_0') or '_label_' in item['prop']['name']
            ]
            values = [item for item in spec['controls'] if '_value_' in item['prop']['name']]
            self.assertGreater(len(values), 0)
            self.assertEqual(len({item['prop']['x'] for item in labels}), 1)
            self.assertEqual(len({item['prop']['x'] for item in values}), 1)
            self.assertGreater(values[0]['prop']['x'], labels[0]['prop']['x'])
            file_ys = [
                item['prop']['y'] for item in spec['controls']
                if item['prop']['name'].startswith('file_label_')
            ]
            gaps = [b - a for a, b in zip(file_ys, file_ys[1:])]
            if gaps:
                self.assertEqual(len(set(gaps)), 1)

    def test_header_pills_path_and_colors(self):
        info = _saved_info(status='modified, read-only', size_memory='1.0 kB')
        for theme, dark in ((dark_theme(), True), (light_theme(), False)):
            spec = build_file_info_dialog(info, theme)
            self.assertEqual(spec['palette']['dark'], dark)
            self.assertEqual(spec['header']['folder'], '/home/scott/projects/cudatext_plugins/cuda-tabmenu')
            self.assertNotIn('logic.py', spec['header']['folder'])
            path = _control(spec, 'path')
            self.assertEqual(path['type'], 'edit')
            self.assertEqual(path['prop']['val'], spec['header']['folder'])
            self.assertTrue(path['prop']['ex0'])
            self.assertFalse(path['prop']['ex2'])
            self.assertEqual(path['prop']['font_color'], spec['palette']['muted'])
            filename = _control(spec, 'filename')
            self.assertEqual(filename['prop']['cap'], 'logic.py')
            self.assertEqual(filename['prop']['font_style'], 'b')
            self.assertGreater(filename['prop']['font_size'], 10)
            self.assertEqual(filename['prop']['font_color'], spec['palette']['text'])
            accent = _control(spec, 'accent')
            self.assertEqual(accent['type'], 'colorpanel')
            self.assertEqual(accent['prop']['x'], 0)
            self.assertLessEqual(accent['prop']['w'], 6)
            self.assertGreater(accent['prop']['h'], path['prop']['y'])
            self.assertEqual(accent['prop']['ex1'], file_info_status_colors(dark, 'modified')['accent'])
            red, green, blue = rgb_from_bgr(accent['prop']['ex1'])
            self.assertGreater(red, green)
            self.assertGreater(green, blue)
            status = _control(spec, 'pill_status')
            readonly = _control(spec, 'pill_readonly')
            self.assertEqual(status['prop']['cap'], 'Modified')
            self.assertEqual(readonly['prop']['cap'], 'Read-only')
            self.assertGreater(readonly['prop']['x'], status['prop']['x'])
            self.assertLessEqual(filename['prop']['x'] + filename['prop']['w'], status['prop']['x'])
            fill_r, fill_g, fill_b = rgb_from_bgr(status['prop']['ex1'])
            self.assertGreater(fill_r, fill_g)
            self.assertGreater(fill_g, fill_b)
            self.assertEqual(status['prop']['ex1'], file_info_status_colors(dark, 'modified')['fill'])
            self.assertEqual(status['prop']['ex2'], file_info_status_colors(dark, 'modified')['text'])
            close = _control(spec, 'btn_close')
            copy = _control(spec, 'btn_copy')
            self.assertEqual(close['type'], 'button_ex')
            self.assertEqual(copy['type'], 'button_ex')
            self.assertNotIn('&', close['prop']['cap'])
            self.assertNotIn('&', copy['prop']['cap'])
            self.assertNotIn('ex0', close['prop'])
            self.assertNotIn('ex0', copy['prop'])
            self.assertTrue(close['focusable'])
            self.assertTrue(copy['focusable'])
            self.assertTrue(spec['keypreview'])
            self.assertEqual(spec['focus'], 'btn_close')
            self.assertTrue(spec['resizable'])
            self.assertEqual(spec['min_height'], spec['height'])
            self.assertEqual(spec['controls'][0]['role'], 'close')
            self.assertEqual(spec['controls'][1]['role'], 'copy')
            self.assertEqual(close['prop']['y'], copy['prop']['y'])
            self.assertGreater(close['prop']['x'], copy['prop']['x'])

        plain = build_file_info_dialog(_saved_info(), None)
        self.assertEqual(_control(plain, 'pill_status')['prop']['cap'], 'Saved')
        self.assertFalse(any(item['prop']['name'] == 'pill_readonly' for item in plain['controls']))
        red, green, blue = rgb_from_bgr(_control(plain, 'accent')['prop']['ex1'])
        self.assertGreater(green, red)
        self.assertGreater(green, blue)

        unsaved = build_file_info_dialog({
            'path': '(unsaved)',
            'filename': 'notes',
            'status': 'unsaved, read-only',
            'encoding': 'utf-8',
            'line_endings': '(none)',
            'lexer': '(none)',
            'size_memory': '0 B',
        }, dark_theme())
        self.assertEqual(_control(unsaved, 'path')['prop']['val'], '(Unsaved)')
        self.assertEqual(_control(unsaved, 'pill_status')['prop']['cap'], 'Unsaved')
        self.assertEqual(_control(unsaved, 'pill_readonly')['prop']['cap'], 'Read-only')
        channels = rgb_from_bgr(_control(unsaved, 'pill_status')['prop']['ex1'])
        self.assertLess(max(channels) - min(channels), 30)

    def test_long_path_stays_inside_the_dialog(self):
        folder = '/home/scott/' + ('deep/' * 40)
        path = folder + 'notes.txt'
        spec = build_file_info_dialog(_saved_info(path=path, filename='notes.txt'), dark_theme())
        self.assertEqual(spec['width'], 520)
        path_ctl = _control(spec, 'path')
        self.assertEqual(path_ctl['prop']['val'], folder.rstrip('/'))
        self.assertGreater(len(path_ctl['prop']['val']), 200)
        self.assertLessEqual(path_ctl['prop']['x'] + path_ctl['prop']['w'], spec['width'])
        self.assertEqual(path_ctl['prop']['a_r'], ('', ']'))
        self._assert_inside(spec)

    def test_custom_captions_and_empty_info(self):
        spec = build_file_info_dialog(
            {'status': 'unsaved', 'filename': 'Draft'},
            captions={'close': 'Fermer', 'copy': 'Copier', 'unsaved': '(Non enregistre)'},
        )
        self.assertEqual(_control(spec, 'btn_close')['prop']['cap'], 'Fermer')
        self.assertEqual(_control(spec, 'btn_copy')['prop']['cap'], 'Copier')
        stripped = build_file_info_dialog(
            {'status': 'saved', 'filename': 'a.txt', 'path': '/tmp/a.txt'},
            captions={'close': '&Close', 'copy': '&Copy Info'},
        )
        self.assertEqual(_control(stripped, 'btn_close')['prop']['cap'], 'Close')
        self.assertEqual(_control(stripped, 'btn_copy')['prop']['cap'], 'Copy Info')
        plain = build_file_info_dialog({'status': 'saved', 'filename': 'a.txt', 'path': '/tmp/a.txt'})
        self.assertEqual(_control(plain, 'btn_close')['prop']['cap'], 'Close')
        self.assertEqual(_control(plain, 'btn_copy')['prop']['cap'], 'Copy Info')
        self.assertEqual(_control(spec, 'path')['prop']['val'], '(Non enregistre)')
        self.assertEqual(spec['copy_text'], format_file_info({'status': 'unsaved', 'filename': 'Draft'}))
        empty = build_file_info_dialog({}, None)
        self.assertEqual(empty['copy_text'], '')
        self._assert_inside(empty)

    def test_host_keeps_scale_focus_and_plain_copy(self):
        text = INIT_PY.read_text(encoding='utf-8')
        self.assertIn('build_file_info_dialog', text)
        self.assertIn('PROC_THEME_UI_DICT_GET', text)
        self.assertIn('DBORDER_SIZE', text)
        self.assertIn('DLG_SCALE', text)
        self.assertIn("DLG_CTL_FOCUS, name='btn_close'", text)
        self.assertIn('PROC_SET_CLIP', text)
        self.assertIn('self._dialog_text', text)
        self.assertIn('BTN_SET_FOCUSABLE', text)
        self.assertIn('DLG_CTL_HANDLE', text)
        self.assertIn("'on_key_down': self._info_key_down", text)
        self.assertIn("prop['on_change'] = self._info_close", text)
        self.assertIn("prop['on_change'] = self._info_copy", text)
        self.assertIn('file_info_key_action', text)
        self.assertNotIn('memo_info', text)
        self.assertNotIn("prop='memo'", text)
        self.assertNotIn("'&Close'", text)
        self.assertNotIn("'&Copy Info'", text)


class ButtonAndKeyTests(unittest.TestCase):
    def test_button_ex_labels_drop_accelerators(self):
        self.assertEqual(button_ex_label('&Close'), 'Close')
        self.assertEqual(button_ex_label('&Copy Info'), 'Copy Info')
        self.assertEqual(button_ex_label('Save && Copy'), 'Save  Copy')
        self.assertEqual(button_ex_label(None), '')
        self.assertNotIn('&', button_ex_label('&Close') + button_ex_label('&Copy Info'))

    def test_buttons_are_theme_controls_anchored_bottom_right(self):
        spec = build_file_info_dialog(_saved_info(), dark_theme())
        close = _control(spec, 'btn_close')
        copy = _control(spec, 'btn_copy')
        self.assertEqual([item['type'] for item in spec['controls'][:2]], ['button_ex', 'button_ex'])
        self.assertEqual(close['role'], 'close')
        self.assertEqual(copy['role'], 'copy')
        self.assertIsNone(close['prop']['a_l'])
        self.assertIsNone(close['prop']['a_t'])
        self.assertEqual(close['prop']['a_r'], ('', ']'))
        self.assertEqual(close['prop']['a_b'], ('', ']'))
        self.assertEqual(copy['prop']['a_r'], ('btn_close', '['))
        self.assertEqual(copy['prop']['a_b'], ('', ']'))
        self.assertGreater(close['prop']['x'], copy['prop']['x'])
        self.assertEqual(close['prop']['y'], copy['prop']['y'])
        self.assertGreater(close['prop']['w'], 0)
        self.assertGreater(copy['prop']['w'], len('Copy Info') * 6)
        self.assertTrue(spec['keypreview'])
        self.assertEqual(spec['focus'], 'btn_close')
        self.assertNotIn('&', close['prop']['cap'] + copy['prop']['cap'])

    def test_escape_closes_and_ctrl_c_stays_with_the_path(self):
        self.assertEqual(file_info_key_action(KEY_ESCAPE, ''), 'close')
        self.assertEqual(file_info_key_action(27, ''), 'close')
        self.assertIsNone(file_info_key_action(KEY_ESCAPE, 's'))
        self.assertIsNone(file_info_key_action(KEY_ESCAPE, 'c'))
        self.assertIsNone(file_info_key_action(KEY_ESCAPE, 'a'))
        # Enter is the focused button_ex's own click, not a form-level close.
        self.assertIsNone(file_info_key_action(KEY_RETURN, ''))
        self.assertIsNone(file_info_key_action(13, 'c'))
        # Ctrl+C copies the path selection. It must not become Copy Info.
        self.assertIsNone(file_info_key_action(KEY_C, 'c'))
        self.assertIsNone(file_info_key_action(ord('C'), 'c'))
        self.assertIsNone(file_info_key_action(KEY_C, 'sc'))
        self.assertIsNone(file_info_key_action(KEY_C, ''))
        self.assertIsNone(file_info_key_action('nope', ''))
        self.assertIsNone(file_info_key_action(None, 'c'))


if __name__ == '__main__':
    unittest.main()
