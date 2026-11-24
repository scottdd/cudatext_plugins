import tempfile
import unittest
from pathlib import Path

from release_plugin import notes_from_history


ROOT = Path(__file__).resolve().parents[2]


def _notes(text: str, **kwargs) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "history.txt"
        path.write_text(text, encoding="utf-8")
        return notes_from_history(path, **kwargs)


class NotesFromHistoryTests(unittest.TestCase):
    def test_long_block_is_complete_and_older_block_is_excluded(self):
        current = ["0.9.0 (2026-11-24)"] + [f"change {i}" for i in range(1, 13)]
        older = [
            "",
            "0.8.0 (2026-11-01)",
            "older first line that must not bleed in",
            "older middle line",
            "older last line that must not be clipped in",
        ]
        self.assertGreater(len(current), 8)
        notes = _notes("\n".join(current + older) + "\n", max_lines=8)
        self.assertEqual(notes, "\n".join(current))
        for line in older:
            if line.strip():
                self.assertNotIn(line, notes)

    def test_older_block_inside_the_old_line_cap_is_not_bled_in_or_clipped(self):
        # The previous 8-line slice started this older block and dropped its last line.
        lines = [
            "0.7.2 (2026-11-24)",
            "newest a",
            "newest b",
            "newest c",
            "",
            "0.7.1 (2026-11-23)",
            "older a",
            "older b",
            "older last line that the old cap dropped",
            "",
            "0.7.0 (2026-11-23)",
            "even older first line",
            "even older last line",
        ]
        notes = _notes("\n".join(lines) + "\n", max_lines=8)
        self.assertEqual(
            notes,
            "0.7.2 (2026-11-24)\nnewest a\nnewest b\nnewest c",
        )
        self.assertNotIn("0.7.1 (2026-11-23)", notes)
        self.assertNotIn("older a", notes)
        self.assertNotIn("older b", notes)
        self.assertNotIn("older last line that the old cap dropped", notes)
        self.assertNotIn("0.7.0 (2026-11-23)", notes)
        self.assertNotIn("even older first line", notes)
        self.assertNotIn("even older last line", notes)

    def test_tab_menu_history_stops_on_the_version_boundary(self):
        history_path = ROOT / "cuda-tabmenu" / "readme" / "history.txt"
        history = history_path.read_text(encoding="utf-8")
        notes = notes_from_history(history_path, max_lines=8)
        self.assertEqual(
            notes,
            "0.7.2 (2026-11-24)\n"
            "tab menu items show the hotkey currently assigned to each Plugins command\n"
            "the shortcut is drawn in the caption; the Plugins menu item keeps the real ShortCut\n"
            "the tab popup's numeric handle is resolved at startup, before the first right-click, "
            "so ASCII Tools can add its submenu beside these items",
        )
        self.assertNotIn("0.7.1 (2026-11-23)", notes)
        self.assertNotIn("Copy Info still copies the plain-text summary", notes)
        self.assertNotIn("File Info dialog:", notes)

        older = history[history.index("0.7.0 (2026-11-23)"):]
        long_notes = _notes(older, max_lines=8)
        self.assertGreater(len(long_notes.splitlines()), 8)
        self.assertTrue(long_notes.startswith("0.7.0 (2026-11-23)\n"))
        self.assertTrue(
            long_notes.endswith(
                "version 0.7.0 sorts after 0.6.3 so Addon Manager can upgrade an existing install"
            )
        )
        self.assertNotIn("0.6.3 (2026-09-15)", long_notes)
        self.assertNotIn("pack a flat plugin zip", long_notes)
        self.assertNotIn("fix tab right-click items", long_notes)


if __name__ == "__main__":
    unittest.main()
