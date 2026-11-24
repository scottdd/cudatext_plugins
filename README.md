# cudatext_plugins

Independent [CudaText](https://cudatext.github.io/) plugins by [scottdd](https://github.com/scottdd). Add the ones you want from a single Addon Manager channel.

## What Is cudatext_plugins?

This is a small collection of CudaText plugins published together, separate from CudaText’s official addon list. Each plugin installs and updates on its own. Use the collection when you want file actions on a tab, help cleaning up text pasted from Word or the web, or updates for add-ons that came from a user channel as well as the official list.

| Plugin | Version | What it does |
|--------|---------|--------------|
| [ASCII Tools](cuda-asciitools/README.md) | 0.2.0 | Find non-ASCII characters, and turn smart punctuation into plain ASCII |
| [Tab Menu](cuda-tabmenu/README.md) | 0.7.2 | Right-click a tab to see file info, reveal the file, or open a folder or terminal |
| [Addons Update](addon_update/README.md) | 0.1.1 | Hear about and install add-on updates, including add-ons from user channels |

## How to Install

> [!WARNING]
> **Only add channels you trust.** Adding a user channel lets CudaText download and run Python code from this repository with **your user permissions**. Future updates also come from this channel. The code is provided **as-is, with no warranty** ([MPL-2.0](https://www.mozilla.org/MPL/2.0/)). Please review the [source](https://github.com/scottdd/cudatext_plugins) and [releases](https://github.com/scottdd/cudatext_plugins/releases) before installing.

### Quick install

1. In CudaText open **Options → Settings-plugins → Addons Manager → Config...**
2. In the **User channels:** box, add this line:

   ```
   https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json
   ```

3. Click OK, then **Plugins → Addons Manager → Install...** and pick the plugins you want.

The channel file lists **published** release zips. A change on `main` is not installed until that plugin is released and the channel file is updated.

On [GitHub Releases](https://github.com/scottdd/cudatext_plugins/releases), the Latest badge is whichever plugin was published most recently. Install from the user channel above, or open the release for the plugin you want.

### Manual install

1. Download `plugin.<Name>.zip` from [GitHub Releases](https://github.com/scottdd/cudatext_plugins/releases).
2. Open the zip in CudaText (**File → Open**). CudaText offers to install it; confirm.
   The zips are flat (`install.inf` at the archive root). If you unzip by hand, extract into `py/<module>/` from the table below so `install.inf` sits directly in that folder. Do not leave the files loose in `py/`, and do not add an extra nested folder.
3. Restart CudaText, or use **Plugins → Reload plugins**.

| Platform | `py` folder | Python |
|----------|-------------|--------|
| Windows | `<folder containing cudatext.exe>\py\` (Windows builds are portable; this is **not** `%APPDATA%`) | Bundled with CudaText |
| macOS | `~/Library/Application Support/CudaText/py/` | Install Python 3 |
| Linux | `~/.config/cudatext/py/` (or `$XDG_CONFIG_HOME/cudatext/py/`) | Install Python 3 |
| Portable (.xz archives, any exe next to a `data/` folder) | `<CudaText exe folder>/py/` | Same as platform |

On macOS and Linux, CudaText needs a system Python 3 to run plugins. Windows builds include it.

| Plugin | Zip | Folder under `py/` |
|--------|-----|--------------------|
| ASCII Tools | `plugin.ASCII_Tools.zip` | `cuda_asciitools` |
| Tab Menu | `plugin.Tab_Menu.zip` | `cuda_tabmenu` |
| Addons Update | `plugin.Addons_Update.zip` | `cuda_addon_update` |

### Updating

Install updates from **Plugins → Addons Manager**, or install [Addons Update](addon_update/README.md) to have checks run on a timer.

If you already have Tab Menu **0.6.3**, version **0.7.0** and later are file actions only. Highlight, find, list, strip, normalize, and transliterate moved to [ASCII Tools](cuda-asciitools/README.md), and `Alt+F3` / `Alt+Shift+F3` moved with them. Addon Manager can upgrade Tab Menu (0.7.0 is newer than 0.6.3). After that upgrade, install ASCII Tools from the same channel if you still want the character tools.

## Changelog

Each plugin’s changes are in its `readme/history.txt`:

- [ASCII Tools](cuda-asciitools/readme/history.txt)
- [Tab Menu](cuda-tabmenu/readme/history.txt)
- [Addons Update](addon_update/readme/history.txt)

Published zips are on [GitHub Releases](https://github.com/scottdd/cudatext_plugins/releases).

## License

[Mozilla Public License 2.0](LICENSE).

## For developers

For building, testing, and releasing, see [DEVELOPERS.md](DEVELOPERS.md).
