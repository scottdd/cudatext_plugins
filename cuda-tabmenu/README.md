# Tab Menu (cuda_tabmenu)

CudaText plugin that adds file actions to the tab right-click menu. Each action uses the tab you clicked. **Plugins → Tab Menu** (and the File Info hotkey) use the focused editor instead.

**Version:** 0.7.2
**Author:** Scott ([scottdd](https://github.com/scottdd))

## Upgrade from 0.6.3

**Non-ASCII tools moved to [ASCII Tools](../cuda-asciitools/) (`cuda-asciitools`).** Tab Menu 0.7.0 does not highlight, find, list, strip, or transliterate characters, and it no longer adds a Search menu.

`0.7.0` sorts after `0.6.3`, so Addon Manager can upgrade an install that came from the user channel. After that upgrade, install **ASCII Tools** from the same channel if you still want those commands (`Alt+F3` and `Alt+Shift+F3` move with them).

## Quick install

1. In CudaText open **Options → Settings-plugins → Addons Manager → Config...**
2. In **User channels:** add:

   ```
   https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json
   ```

3. Click OK, then **Plugins → Addons Manager → Install...** and choose **Tab Menu**.

> [!WARNING]
> **Only add channels you trust.** A user channel lets CudaText download and run Python from this repository with **your user permissions**. Later updates come from the same channel. The code is provided **as-is, with no warranty** ([MPL-2.0](https://www.mozilla.org/MPL/2.0/)). Please review the [source](https://github.com/scottdd/cudatext_plugins) and [releases](https://github.com/scottdd/cudatext_plugins/releases) before installing.

The channel lists **published** releases. This repository’s `main` branch is not itself the channel payload.

## Commands

On the tab you right-clicked, items that need a file on disk are disabled for unsaved tabs. The Plugins menu entries are enabled; running one on an unsaved tab reports that there is no file.

| Command | Hotkey | Notes |
|---------|--------|--------|
| File Info... | `Ctrl+Shift+Alt+I` | Themed dialog: filename, folder, status (saved / modified / unsaved, and read-only), encoding, line endings, lexer, size on disk, size in memory when modified or unsaved (UTF-8 bytes), lines, words, characters, last modified time. **Copy Info** copies the same plain-text summary. |
| Reveal in File Manager | | Windows `explorer /select,<path>`, macOS `open -R`, Linux `org.freedesktop.FileManager1.ShowItems` with a fallback of `xdg-open` on the folder. Disabled if unsaved. |
| Open Folder | | Opens the file’s folder in the file manager. Disabled if unsaved. |
| Open Terminal Here | | Windows Terminal (`wt -d`) or `cmd`, macOS Terminal, or the first common Linux terminal on `PATH`. Disabled if unsaved. |
| Reopen / Reload from Disk | | `cmd_FileReopen` on the clicked tab. Disabled if unsaved. |
| Save a Copy As... | | Writes this tab’s contents to a path you choose. The open tab keeps its filename and modified flag. |
| Duplicate File | | Asks for a name in the same folder, defaulting to a free `stem_copy.ext` (`stem_copy2.ext`, …). Writes it and opens the new file. An unmodified tab is copied byte for byte; a modified tab writes the buffer. Disabled if unsaved. |
| Close and Delete File... | | Confirms with the full path, closes the tab, and deletes the file permanently (not the trash). Disabled if unsaved. |
| Export to HTML... | | `cmd_FileExportHtml` on the clicked text tab. |

CudaText already has Close, Close others / all / left / right, Rename, Save, Save As, Copy full path / folder / filename, Move tab to group, Pinned, and Set tab color. This plugin does not add those again.

Tab-menu commands are bound to the plugin `Command` instance. The numeric tab-popup handle is cached when the plugin starts, before the first right-click, so a later update does not rebuild the stock menu and wipe items added by this plugin or by ASCII Tools. Each item shows the hotkey currently assigned to its Plugins command (Command Palette, F9). Pressing the key runs that command on the focused editor. Errors are printed to the Console (stdout).

## Manual install

1. Download `plugin.Tab_Menu.zip` from [Releases](https://github.com/scottdd/cudatext_plugins/releases), or run `./pack.sh` (`dist/plugin.Tab_Menu.zip`).
2. In CudaText choose **File → Open**, open the zip, and confirm the install.
3. Restart CudaText, or use **Plugins → Reload plugins**.

The zip is **flat**: `install.inf` is at the root of the archive. Opening it in CudaText installs into `py/cuda_tabmenu/`. If you unzip yourself, extract into that folder so `install.inf` is directly inside it.

| Platform | `py` folder | Python |
|----------|-------------|--------|
| Windows | `<folder containing cudatext.exe>\py\` (Windows builds are portable; this is **not** `%APPDATA%`) | Bundled with CudaText |
| macOS | `~/Library/Application Support/CudaText/py/` | Install Python 3 |
| Linux | `~/.config/cudatext/py/` (or `$XDG_CONFIG_HOME/cudatext/py/`) | Install Python 3 |
| Portable (.xz archives, any exe next to a `data/` folder) | `<CudaText exe folder>/py/` | Same as the platform |

### From this monorepo

```bash
ln -sfn ~/Projects/cudatext_plugins/cuda-tabmenu ~/.config/cudatext/py/cuda_tabmenu
```

Addon Manager **Install from GitHub** only works when the repository root name matches `subdir=`. For this monorepo, use the zip, the user channel, or a symlink.

## Tests

From the monorepo root:

```bash
python3 -m unittest discover -s cuda-tabmenu/tests -t cuda-tabmenu
```

## License

[Mozilla Public License 2.0](LICENSE).
