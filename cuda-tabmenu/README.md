# Tab Menu

CudaText plugin that adds file actions to the tab right-click menu. Each action uses the tab you clicked.

**Version:** 0.7.2
**Author:** Scott ([scottdd](https://github.com/scottdd))

## What Is Tab Menu?

Right-click a tab to reveal that file, open a terminal in its folder, or read file info, without hunting through the File menu. The same commands are under **Plugins → Tab Menu**, where they use the editor that has focus. The File Info hotkey does too.

Items that need a file on disk are greyed out on an unsaved tab. The Plugins menu still lists them; running one there on an unsaved tab reports that there is no file.

Each tab-menu item shows the hotkey assigned to that command right now, including a key you set in the Command Palette (`F9`). Only File Info has a default. Pressing a key runs the command on the focused editor. Choosing the item in the tab menu uses the tab you clicked.

| Command | Default hotkey | What it does |
|---------|----------------|--------------|
| File Info... | `Ctrl+Shift+Alt+I` | Dialog for filename, folder, status (saved, modified, or unsaved, and read-only), encoding, line endings, lexer, size on disk, size in memory when modified or unsaved (UTF-8), lines, words, characters, and last modified time. The dialog follows the UI theme. **Copy Info** copies that summary as plain text. Close starts focused. Escape closes the dialog. |
| Reveal in File Manager | | Selects the file in the system file manager. Windows uses `explorer /select,<path>`, macOS uses `open -R`, and Linux uses `org.freedesktop.FileManager1.ShowItems` with a fallback of `xdg-open` on the folder. Unavailable when unsaved. |
| Open Folder | | Opens the file’s folder. Unavailable when unsaved. |
| Open Terminal Here | | A terminal in that folder: Windows Terminal (`wt -d`) or `cmd`, macOS Terminal, or the first common Linux terminal on `PATH`. Unavailable when unsaved. |
| Reopen / Reload from Disk | | CudaText’s Reopen command on the clicked tab. Unavailable when unsaved. |
| Save a Copy As... | | Writes this tab’s contents to a path you choose. The open tab keeps its filename and modified state. |
| Duplicate File | | Asks for a name in the same folder. The suggestion is a free `stem_copy.ext`, then `stem_copy2.ext`, and so on. Writes the file and opens it. An unmodified tab is copied byte for byte. A modified tab writes the buffer. Unavailable when unsaved. |
| Close and Delete File... | | Shows the full path and asks before it closes the tab and deletes the file permanently (it does not go to the trash). Unavailable when unsaved. |
| Export to HTML... | | Exports the clicked text tab to HTML. |

CudaText already has Close, Close others, Close all, close to the left or right, Rename, Save, Save As, copy full path / folder / filename, move tab to another group, Pinned, and Set tab color. Tab Menu does not add those again.

If a command fails, the error is printed to the Console.

## How to Install

> [!WARNING]
> **Only add channels you trust.** Adding a user channel lets CudaText download and run Python code from this repository with **your user permissions**. Future updates also come from this channel. The code is provided **as-is, with no warranty** ([MPL-2.0](https://www.mozilla.org/MPL/2.0/)). Please review the [source](https://github.com/scottdd/cudatext_plugins) and [releases](https://github.com/scottdd/cudatext_plugins/releases) before installing.

### Quick install

1. In CudaText open **Options → Settings-plugins → Addons Manager → Config...**
2. In the **User channels:** box, add this line:

   ```
   https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json
   ```

3. Click OK, then **Plugins → Addons Manager → Install...** and choose **Tab Menu**.

The channel file lists **published** release zips. A change on `main` is not installed until that plugin is released and the channel file is updated. The same channel installs the other plugins in this [collection](../README.md).

### Manual install

1. Download `plugin.Tab_Menu.zip` from [GitHub Releases](https://github.com/scottdd/cudatext_plugins/releases).
2. Open the zip in CudaText (**File → Open**). CudaText offers to install it; confirm.
   The zip is flat (`install.inf` at the archive root). CudaText places that root in `py/cuda_tabmenu/`. If you unzip by hand, extract into `py/cuda_tabmenu/` so `install.inf` sits directly in that folder. Do not leave the files loose in `py/`, and do not add an extra nested folder.
3. Restart CudaText, or use **Plugins → Reload plugins**.

| Platform | `py` folder | Python |
|----------|-------------|--------|
| Windows | `<folder containing cudatext.exe>\py\` (Windows builds are portable; this is **not** `%APPDATA%`) | Bundled with CudaText |
| macOS | `~/Library/Application Support/CudaText/py/` | Install Python 3 |
| Linux | `~/.config/cudatext/py/` (or `$XDG_CONFIG_HOME/cudatext/py/`) | Install Python 3 |
| Portable (.xz archives, any exe next to a `data/` folder) | `<CudaText exe folder>/py/` | Same as platform |

On macOS and Linux, CudaText needs a system Python 3 to run plugins. Windows builds include it.

### Updating from 0.6.3

Tab Menu **0.7.0** and later are file actions only. Non-ASCII tools moved to [ASCII Tools](../cuda-asciitools/README.md): highlight, next and previous (`Alt+F3`, `Alt+Shift+F3`), list, strip, normalize, and transliterate. Tab Menu no longer adds a Search menu.

Addon Manager can upgrade an existing install, because 0.7.0 is newer than 0.6.3. After that upgrade, install ASCII Tools from the same user channel if you still want the character tools.

## Changelog

[readme/history.txt](readme/history.txt) and [GitHub Releases](https://github.com/scottdd/cudatext_plugins/releases).

## License

[Mozilla Public License 2.0](LICENSE).

## For developers

For building, testing, and releasing, see [DEVELOPERS.md](DEVELOPERS.md).
