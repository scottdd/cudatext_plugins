import unittest

from anyascii import anyascii
from logic import (
    collect_nonascii_positions,
    count_words,
    find_next_nonascii,
    find_prev_nonascii,
    finder_wrap_enabled,
    format_size,
    is_non_ascii_char,
)


class FormatSizeTests(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(format_size(0), '0 B')

    def test_bytes(self):
        self.assertEqual(format_size(512), '512.0 B')

    def test_kilobytes(self):
        self.assertEqual(format_size(2048), '2.0 kB')


class CountWordsTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(count_words(''), 0)

    def test_simple(self):
        self.assertEqual(count_words('hello world'), 2)

    def test_extra_space(self):
        self.assertEqual(count_words('  one   two\nthree  '), 3)


class NonAsciiSearchTests(unittest.TestCase):
    def test_ascii_only_is_false(self):
        self.assertFalse(is_non_ascii_char('A'))
        self.assertTrue(is_non_ascii_char('é'))

    def test_collect_positions(self):
        xs, ys, lens = collect_nonascii_positions(['abc', 'café', 'ü'])
        self.assertEqual(xs, [3, 0])
        self.assertEqual(ys, [1, 2])
        self.assertEqual(lens, [1, 1])

    def test_next_without_wrap(self):
        lines = ['abc', 'café', 'xyz']
        self.assertEqual(find_next_nonascii(lines, 0, 0, wrap=False), (3, 1, False))
        self.assertIsNone(find_next_nonascii(lines, 3, 1, wrap=False))

    def test_next_wraps_to_first(self):
        lines = ['ä', 'b', 'ü']
        self.assertEqual(find_next_nonascii(lines, 0, 2, wrap=True), (0, 0, True))

    def test_next_wrap_only_match_is_current(self):
        lines = ['abc', 'café']
        self.assertEqual(find_next_nonascii(lines, 3, 1, wrap=True), (3, 1, True))

    def test_next_wrap_finds_nothing(self):
        self.assertIsNone(find_next_nonascii(['abc'], 0, 0, wrap=True))

    def test_prev_without_wrap(self):
        lines = ['ä', 'b', 'ü']
        self.assertEqual(find_prev_nonascii(lines, 0, 2, wrap=False), (0, 0, False))
        self.assertIsNone(find_prev_nonascii(lines, 0, 0, wrap=False))

    def test_prev_wraps_to_last(self):
        lines = ['ä', 'b', 'ü']
        self.assertEqual(find_prev_nonascii(lines, 0, 0, wrap=True), (0, 2, True))

    def test_empty_document(self):
        self.assertIsNone(find_next_nonascii([], 0, 0, wrap=True))
        self.assertIsNone(find_prev_nonascii([], 0, 0, wrap=True))


class FinderWrapTests(unittest.TestCase):
    def test_missing_prop(self):
        self.assertFalse(finder_wrap_enabled(None))
        self.assertFalse(finder_wrap_enabled('a'))
        self.assertFalse(finder_wrap_enabled({}))

    def test_persisted_flag(self):
        self.assertTrue(finder_wrap_enabled({'op_wrap': True}))
        self.assertFalse(finder_wrap_enabled({'op_wrap': False}))

    def test_dialog_flag_wins(self):
        self.assertFalse(finder_wrap_enabled({'op_wrap': True, 'op_wrap_d': False}))
        self.assertTrue(finder_wrap_enabled({'op_wrap': False, 'op_wrap_d': True}))


class AnyAsciiSmokeTests(unittest.TestCase):
    def test_transliterate(self):
        self.assertEqual(anyascii('café'), 'cafe')
        self.assertEqual(anyascii('ascii'), 'ascii')


if __name__ == '__main__':
    unittest.main()
