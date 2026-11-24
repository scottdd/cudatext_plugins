Plugin for CudaText: ASCII Tools (cuda_asciitools)
Version 0.2.0
Author: Scott (https://github.com/scottdd)

ASCII Tools finds non-ASCII characters, lists them, and turns common
Unicode punctuation into plain ASCII. Accented letters are only changed
when you explicitly transliterate or strip them.

These commands used to live in Tab Menu. Tab Menu 0.7.0 is file actions
only. Install this plugin if you want the non-ASCII tools.

QUICK INSTALL
  Options → Settings-plugins → Addons Manager → Config...
  User channels: add this line:

    https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json

  Then Plugins → Addons Manager → Install... and choose ASCII Tools.

TRUST
  Only add channels you trust. A user channel lets CudaText download and
  run Python from that repository with your user permissions. Future
  updates come from the same channel. The code is provided as-is, with
  no warranty (MPL-2.0). Please review the source and releases first:
    https://github.com/scottdd/cudatext_plugins

WHAT IT DOES
  Plugins → ASCII Tools, Search → ASCII Tools, and the tab you right-click
  (ASCII Tools). The tab submenu runs on the tab you clicked. Plugins,
  Search, the Command Palette, and the key itself use the focused editor.
  A non-text tab shows the submenu disabled.

  Search and the tab submenu show the hotkey currently assigned to each
  command (Command Palette, F9). Pressing the key still runs once.

  - Highlight Non-ASCII
      Marks code points above 127. While highlighting is on, edits refresh
      the marks (on_change_slow).
  - Un-highlight Non-ASCII
  - Next Non-ASCII Character          Alt+F3
  - Previous Non-ASCII Character      Alt+Shift+F3
      Both honor Find's "Wrapped search" option (O), the same toggle F3 uses.
      The status bar says "Wrapped search" when the search crosses the edge.
  - List Non-ASCII Characters
      Selection if any text is selected, otherwise the whole document.
      Each row shows line, column (1-based), the character, U+XXXX, and
      the Unicode name, plus a count. Copy puts the report on the clipboard.
      Open in Tab puts it in a new scratch tab.
  - Transliterate to ASCII
      Uses the bundled AnyAscii data. A selection is converted in place.
      With no selection, you confirm, then the whole document is converted.
      Active highlighting is applied again afterward.
  - Strip Non-ASCII Characters
      Deletes code points above 127. Same selection / confirm rules.
  - Normalize Punctuation & Spaces to ASCII
      Smart quotes, primes, en/em dashes, minus, ellipsis, unusual spaces,
      and list bullets become plain ASCII. Zero-width spaces are removed.
      Accented letters (é, ñ, ü, …) stay as they are.

  Whole-document edits keep Undo (the text is replaced, not reloaded).
  Read-only documents are left unchanged.

MANUAL INSTALL
  1. Download plugin.ASCII_Tools.zip from GitHub Releases, or build it
     with ./pack.sh (output: dist/plugin.ASCII_Tools.zip).
  2. In CudaText choose File → Open, open the zip, and confirm install.
     The zip is flat (install.inf at the zip root). Do not wrap it in an
     extra folder. If you unzip by hand, put the files in py/cuda_asciitools/
     so install.inf sits directly in that folder — not loose in py/.
  3. Restart CudaText, or use Plugins → Reload plugins.

  py folder (the install.inf "subdir" is cuda_asciitools):

    Windows   <folder containing cudatext.exe>\py\
              Windows builds are portable. This is NOT %APPDATA%.
    macOS     ~/Library/Application Support/CudaText/py/
    Linux     ~/.config/cudatext/py/
              or $XDG_CONFIG_HOME/cudatext/py/
    Portable  <CudaText exe folder>/py/
              (.xz archives, or any exe next to a data/ folder)

  macOS and Linux need a system Python 3. Windows builds include Python.

Dev symlink (folder name uses an underscore):

  ln -sfn ~/Projects/cudatext_plugins/cuda-asciitools ~/.config/cudatext/py/cuda_asciitools

Do not use Addon Manager "Install from GitHub" on the monorepo root URL.
The repository name does not match subdir=cuda_asciitools.

Homepage: https://github.com/scottdd/cudatext_plugins/tree/main/cuda-asciitools
License: MPL 2.0 (plugin); AnyAscii ISC (anyascii/LICENSE)
