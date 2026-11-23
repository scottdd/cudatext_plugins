Plugin for CudaText: Tab Menu (cuda_tabmenu)
Version 0.7.0
Author: Scott (https://github.com/scottdd)

Right-click a tab for file actions on THAT tab. The same commands are under
Plugins → Tab Menu, where they use the focused editor. Items that need a
file on disk are greyed out when the tab is unsaved.

UPGRADE FROM 0.6.3
  Non-ASCII tools are no longer in Tab Menu. They moved to the separate
  ASCII Tools plugin (cuda-asciitools): highlight, next/previous (Alt+F3,
  Alt+Shift+F3), list, strip, normalize, and transliterate.
  After you upgrade Tab Menu, install ASCII Tools from the user channel
  if you still want those commands.

QUICK INSTALL
  Options → Settings-plugins → Addons Manager → Config...
  User channels: add this line:

    https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json

  Then Plugins → Addons Manager → Install... and choose Tab Menu.
  0.7.0 sorts after 0.6.3, so Addon Manager can upgrade an existing install.
  The channel lists published releases.

TRUST
  Only add channels you trust. A user channel lets CudaText download and
  run Python from that repository with your user permissions. Future
  updates come from the same channel. The code is provided as-is, with
  no warranty (MPL-2.0). Please review the source and releases first:
    https://github.com/scottdd/cudatext_plugins

TAB MENU (clicked tab) AND PLUGINS → TAB MENU (focused tab)
  File Info...                         Ctrl+Shift+Alt+I
      Path, filename, status (unsaved / saved / modified, plus read-only),
      encoding, line endings, lexer, size on disk, size in memory when the
      tab is modified or unsaved (UTF-8), line / word / character counts,
      and last modified time. Copy Info copies that summary.
  Reveal in File Manager
      Windows: explorer /select,<path>
      macOS:   open -R <path>
      Linux:   org.freedesktop.FileManager1.ShowItems, then xdg-open <dir>
      Disabled when unsaved.
  Open Folder
      Opens the file's folder. Disabled when unsaved.
  Open Terminal Here
      A terminal in that folder (Windows Terminal or cmd, macOS Terminal,
      or a common Linux terminal). Disabled when unsaved.
  Reopen / Reload from Disk
      CudaText File → Reopen on the clicked tab. Disabled when unsaved.
  Save a Copy As...
      Writes the tab's contents to a path you choose. The open tab keeps
      its filename and modified state.
  Duplicate File
      Asks for a name in the same folder. The suggestion is stem_copy.ext,
      then stem_copy2.ext, and so on. Writes the file and opens it.
      An unmodified tab is copied byte for byte. A modified tab writes the
      buffer. Disabled when unsaved.
  Close and Delete File...
      Shows the full path and asks before it closes the tab and deletes
      the file permanently (not the trash). Disabled when unsaved.
  Export to HTML...
      Runs cmd_FileExportHtml on the clicked text tab.

  Stock tab items are not repeated: Close, Close others / all / left / right,
  Rename, Save, Save As, Copy path / folder / filename, Move tab to group,
  Pinned, and Set tab color.

MANUAL INSTALL
  1. Download plugin.Tab_Menu.zip from GitHub Releases, or build it with
     ./pack.sh (output: dist/plugin.Tab_Menu.zip).
  2. In CudaText choose File → Open, open the zip, and confirm install.
     The zip is flat (install.inf at the zip root). If you unzip by hand,
     put the files in py/cuda_tabmenu/ so install.inf sits directly in that
     folder — not loose in py/, and not in an extra nested folder.
  3. Restart CudaText, or use Plugins → Reload plugins.

  py folder (the install.inf "subdir" is cuda_tabmenu):

    Windows   <folder containing cudatext.exe>\py\
              Windows builds are portable. This is NOT %APPDATA%.
    macOS     ~/Library/Application Support/CudaText/py/
    Linux     ~/.config/cudatext/py/
              or $XDG_CONFIG_HOME/cudatext/py/
    Portable  <CudaText exe folder>/py/
              (.xz archives, or any exe next to a data/ folder)

  macOS and Linux need a system Python 3. Windows builds include Python.

Dev symlink (folder name uses an underscore):

  ln -sfn ~/Projects/cudatext_plugins/cuda-tabmenu ~/.config/cudatext/py/cuda_tabmenu

Do not use Addon Manager "Install from GitHub" on the monorepo root URL.
The repository name does not match subdir=cuda_tabmenu.

Homepage: https://github.com/scottdd/cudatext_plugins/tree/main/cuda-tabmenu
License: MPL 2.0
