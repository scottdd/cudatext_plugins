Plugin for CudaText: ASCII Tools (cuda_asciitools)
Version 0.2.0
Author: Scott (https://github.com/scottdd)

WHAT IS ASCII TOOLS
  ASCII Tools finds characters outside plain ASCII, jumps to them, lists
  them, and can rewrite the punctuation that word processors and web pages
  insert. Letters such as é, ñ, and ü stay unless you choose Transliterate
  or Strip.

  A common case is a config or source file after a paste from Word or the
  web. Smart quotes and non-breaking spaces are easy to miss. Select the
  pasted text and run "Normalize Punctuation & Spaces to ASCII", or run it
  on the whole document after you confirm.

  These commands used to live in Tab Menu. Tab Menu 0.7.0 and later are
  file actions only. Install ASCII Tools if you still want them, including
  Next on Alt+F3 and Previous on Alt+Shift+F3.

  The same commands are in three places:
    Plugins → ASCII Tools
    Search → ASCII Tools
    the tab you right-click, under ASCII Tools

  The tab submenu runs on the tab you clicked. Plugins, Search, the
  Command Palette, and the hotkey itself use the editor that has focus.
  A tab that is not a text document shows the submenu disabled.

  Search and the tab submenu show the hotkey assigned to each command
  right now, including a key you set in the Command Palette (F9). Pressing
  the key still runs the command once, on the focused editor.

  Highlight Non-ASCII
      Marks characters outside plain ASCII. While this is on, edits
      refresh the marks.
  Un-highlight Non-ASCII
      Clears those marks.
  Next Non-ASCII Character                 Alt+F3
      Selects the next match. Wraps when Find's "Wrapped search" (O) is on.
      The status bar says "Wrapped search" when the search crosses the
      edge of the document.
  Previous Non-ASCII Character             Alt+Shift+F3
      Same wrap rule, searching backward.
  List Non-ASCII Characters
      Line, column (starting at 1), character, U+XXXX, and Unicode name,
      plus a count. Uses the selection when there is one, otherwise the
      whole document. Copy copies the report. Open in Tab puts it in a
      new scratch tab.
  Transliterate to ASCII
      Converts non-ASCII text to ASCII approximations. A selection is
      converted in place. With no selection, you confirm, then the whole
      document is converted.
  Strip Non-ASCII Characters
      Deletes characters outside plain ASCII. Same selection and confirm
      rules.
  Normalize Punctuation & Spaces to ASCII
      Smart quotes, primes, dashes, minus, ellipsis, unusual spaces, and
      list bullets become ASCII. Zero-width spaces are removed. Accented
      letters stay.

  Highlighting is drawn again after a successful transliterate, strip, or
  normalize when it was already on. A change to the whole document can be
  undone. A read-only document is left unchanged.

HOW TO INSTALL

  TRUST
    Only add channels you trust. Adding a user channel lets CudaText
    download and run Python code from this repository with your user
    permissions. Future updates also come from this channel. The code is
    provided as-is, with no warranty (MPL-2.0). Please review the source
    and releases before installing:
      https://github.com/scottdd/cudatext_plugins
      https://github.com/scottdd/cudatext_plugins/releases

  QUICK INSTALL
    1. Options → Settings-plugins → Addons Manager → Config...
    2. In User channels, add this line:

         https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json

    3. Click OK, then Plugins → Addons Manager → Install... and choose
       ASCII Tools.

    The channel lists published release zips. A change on main is not
    installed until this plugin is released and the channel file is
    updated.

    On GitHub Releases, the Latest badge is whichever plugin was published
    most recently. Use the channel above, or open the ASCII Tools release.

  MANUAL INSTALL
    1. Download plugin.ASCII_Tools.zip from GitHub Releases.
    2. In CudaText choose File → Open, open the zip, and confirm.
       The zip is flat (install.inf at the archive root). CudaText places
       that root in py/cuda_asciitools/. If you unzip by hand, extract
       into py/cuda_asciitools/ so install.inf sits directly in that
       folder. Do not leave the files loose in py/, and do not add an
       extra nested folder.
    3. Restart CudaText, or use Plugins → Reload plugins.

    py folder (install folder cuda_asciitools):

      Windows   <folder containing cudatext.exe>\py\
                Windows builds are portable. This is NOT %APPDATA%.
      macOS     ~/Library/Application Support/CudaText/py/
      Linux     ~/.config/cudatext/py/
                or $XDG_CONFIG_HOME/cudatext/py/
      Portable  <CudaText exe folder>/py/
                (.xz archives, or any exe next to a data/ folder)

    macOS and Linux need a system Python 3. Windows builds include Python.

  UPDATING FROM TAB MENU 0.6.3
    Tab Menu 0.7.0 and later do not include these commands. After Tab Menu
    upgrades, install ASCII Tools from the same user channel. Alt+F3 and
    Alt+Shift+F3 belong to this plugin.

Homepage: https://github.com/scottdd/cudatext_plugins/tree/main/cuda-asciitools
License: MPL 2.0 (plugin); AnyAscii ISC (anyascii/LICENSE)
Changelog: readme/history.txt and GitHub Releases
