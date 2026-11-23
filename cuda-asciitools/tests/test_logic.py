import unittest

from anyascii import anyascii
from logic import (
    collect_nonascii_entries,
    collect_nonascii_in_spans,
    collect_nonascii_positions,
    find_next_nonascii,
    find_prev_nonascii,
    finder_wrap_enabled,
    format_nonascii_report,
    is_non_ascii_char,
    normalize_punctuation,
    normalize_selection,
    selections_from_carets,
    strip_nonascii,
)


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


class SelectionTests(unittest.TestCase):
    def test_no_selection(self):
        self.assertIsNone(normalize_selection(1, 2, -1, -1))
        self.assertIsNone(normalize_selection(1, 2, 1, 2))

    def test_orders_backward_selection(self):
        self.assertEqual(normalize_selection(4, 1, 1, 0), (1, 0, 4, 1))

    def test_carets_skip_plain_carets_and_sort(self):
        carets = [
            (0, 2, 3, 2),
            (1, 1, -1, -1),
            (5, 0, 1, 0),
        ]
        self.assertEqual(
            selections_from_carets(carets),
            [(1, 0, 5, 0), (0, 2, 3, 2)],
        )


class ReportTests(unittest.TestCase):
    def test_whole_document_positions_are_one_based(self):
        entries = collect_nonascii_entries(['café', 'über'])
        self.assertEqual([item['char'] for item in entries], ['é', 'ü'])
        self.assertEqual(entries[0]['line'], 1)
        self.assertEqual(entries[0]['column'], 4)
        self.assertEqual(entries[0]['codepoint'], 'U+00E9')
        self.assertIn('LATIN', entries[0]['name'])
        self.assertEqual(entries[1]['line'], 2)
        self.assertEqual(entries[1]['column'], 1)

    def test_span_limits_the_scan(self):
        lines = ['café', 'über']
        entries = collect_nonascii_entries(lines, (2, 0, 1, 1))
        self.assertEqual([item['char'] for item in entries], ['é', 'ü'])

    def test_overlapping_spans_are_reported_once(self):
        lines = ['éé']
        entries = collect_nonascii_in_spans(lines, [(0, 0, 2, 0), (1, 0, 2, 0)])
        self.assertEqual([item['column'] for item in entries], [1, 2])

    def test_empty_spans_mean_whole_document(self):
        entries = collect_nonascii_in_spans(['Aé'], [])
        self.assertEqual(len(entries), 1)

    def test_report_contains_code_point_name_and_count(self):
        entries = collect_nonascii_entries(['café'])
        report = format_nonascii_report(entries, scope='selection')
        self.assertIn('Scope: selection', report)
        self.assertIn('U+00E9', report)
        self.assertIn('LATIN SMALL LETTER E WITH ACUTE', report)
        self.assertTrue(report.endswith('1 non-ASCII character'))

    def test_report_plural_and_invisible_space(self):
        entries = collect_nonascii_entries(['a\u00a0b'])
        report = format_nonascii_report(entries, scope='whole document')
        self.assertIn('<U+00A0>', report)
        self.assertIn('NO-BREAK SPACE', report)
        self.assertTrue(report.endswith('1 non-ASCII character'))

    def test_empty_report(self):
        report = format_nonascii_report([], scope='whole document')
        self.assertIn('Scope: whole document', report)
        self.assertTrue(report.endswith('0 non-ASCII characters'))

    def test_unnamed_private_use(self):
        entries = collect_nonascii_entries(['\ue000'])
        self.assertEqual(entries[0]['name'], '<unnamed>')
        self.assertEqual(entries[0]['codepoint'], 'U+E000')


class TransformTests(unittest.TestCase):
    def test_strip_removes_non_ascii_and_keeps_newlines(self):
        self.assertEqual(strip_nonascii('café\n—x'), 'caf\nx')
        self.assertEqual(strip_nonascii(''), '')
        self.assertEqual(strip_nonascii('ascii'), 'ascii')

    def test_normalize_quotes_dashes_ellipsis_primes(self):
        self.assertEqual(normalize_punctuation('“hello”'), '"hello"')
        self.assertEqual(normalize_punctuation('‘it’'), "'it'")
        self.assertEqual(normalize_punctuation('«quote»'), '"quote"')
        self.assertEqual(normalize_punctuation('‹q›'), "'q'")
        self.assertEqual(normalize_punctuation('a—b–c−d'), 'a--b-c-d')
        self.assertEqual(normalize_punctuation('wait…'), 'wait...')
        self.assertEqual(normalize_punctuation('2′ 3″'), "2' 3\"")

    def test_normalize_spaces_and_bullets(self):
        self.assertEqual(normalize_punctuation('a\u00a0b'), 'a b')
        self.assertEqual(normalize_punctuation('a\u2009b'), 'a b')
        self.assertEqual(normalize_punctuation('a\u200bb'), 'ab')
        self.assertEqual(normalize_punctuation('\ufeffcode'), 'code')
        self.assertEqual(normalize_punctuation('• item'), '- item')
        self.assertEqual(normalize_punctuation('◦ next'), '- next')

    def test_normalize_keeps_accented_letters(self):
        self.assertEqual(normalize_punctuation('Àéïõüç — naïve'), 'Àéïõüç -- naïve')

    def test_normalize_empty(self):
        self.assertEqual(normalize_punctuation(''), '')


class AnyAsciiSmokeTests(unittest.TestCase):
    def test_transliterate(self):
        self.assertEqual(anyascii('café'), 'cafe')
        self.assertEqual(anyascii('ascii'), 'ascii')
        self.assertEqual(anyascii('“hi”'), '"hi"')


if __name__ == '__main__':
    unittest.main()
