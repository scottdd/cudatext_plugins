# ASCII Tools

CudaText plugin that finds non-ASCII characters and converts the punctuation you usually want as plain ASCII. Accented letters stay unless you ask to transliterate or strip them.

**Version:** 0.2.0
**Author:** Scott ([scottdd](https://github.com/scottdd))

## What Is ASCII Tools?

ASCII Tools marks characters outside plain ASCII, jumps to them, lists them, and can rewrite the punctuation that word processors and web pages insert. Letters such as é, ñ, and ü are left alone unless you choose Transliterate or Strip.

A common case is a config or source file after a paste from Word or the web. Smart quotes, non-breaking spaces, and similar characters are easy to miss and awkward to commit. Select the pasted text and run **Normalize Punctuation & Spaces to ASCII**, or run it on the whole document after you confirm.

These commands used to live in Tab Menu. Tab Menu 0.7.0 and later are file actions only. Install ASCII Tools if you still want them, including **Next** on `Alt+F3` and **Previous** on `Alt+Shift+F3`.

The same commands are in three places:

- **Plugins → ASCII Tools**
- **Search → ASCII Tools**
- the tab you right-click, under **ASCII Tools**

The tab submenu runs on the tab you clicked. Plugins, Search, the Command Palette, and the hotkey itself use the editor that has focus. A tab that is not a text document shows the submenu disabled.

Search and the tab submenu show the hotkey assigned to each command right now, including a key you set in the Command Palette (`F9`). Pressing the key still runs the command once, on the focused editor.

| Command | Default hotkey | What it does |
|---------|----------------|--------------|
| Highlight Non-ASCII | | Marks characters outside plain ASCII. While this is on, edits refresh the marks. |
| Un-highlight Non-ASCII | | Clears those marks. |
| Next Non-ASCII Character | `Alt+F3` | Selects the next match. Wraps when Find’s **Wrapped search** (O) is on. |
| Previous Non-ASCII Character | `Alt+Shift+F3` | Same wrap rule, searching backward. |
| List Non-ASCII Characters | | Line, column (starting at 1), character, `U+XXXX`, and Unicode name, plus a count. Uses the selection when there is one, otherwise the whole document. **Copy** copies the report. **Open in Tab** puts it in a new scratch tab. |
| Transliterate to ASCII | | Converts non-ASCII text to ASCII approximations. A selection is converted in place. With no selection, you confirm, then the whole document is converted. |
| Strip Non-ASCII Characters | | Deletes characters outside plain ASCII. Same selection and confirm rules. |
| Normalize Punctuation & Spaces to ASCII | | Smart quotes, primes, dashes, minus, ellipsis, unusual spaces, and list bullets become ASCII. Zero-width spaces are removed. Accented letters stay. |

Highlighting is drawn again after a successful transliterate, strip, or normalize when it was already on. A change to the whole document can be undone. A read-only document is left unchanged.

Next and Previous show `Wrapped search` on the status bar when they cross the edge of the document.

## How to Install

> [!WARNING]
> **Only add channels you trust.** Adding a user channel lets CudaText download and run Python code from this repository with **your user permissions**. Future updates also come from this channel. The code is provided **as-is, with no warranty** ([MPL-2.0](https://www.mozilla.org/MPL/2.0/)). Please review the [source](https://github.com/scottdd/cudatext_plugins) and [releases](https://github.com/scottdd/cudatext_plugins/releases) before installing.

### Quick install

1. In CudaText open **Options → Settings-plugins → Addons Manager → Config...**
2. In the **User channels:** box, add this line:

   ```
   https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json
   ```

3. Click OK, then **Plugins → Addons Manager → Install...** and choose **ASCII Tools**.

The channel file lists **published** release zips. A change on `main` is not installed until that plugin is released and the channel file is updated. The same channel installs the other plugins in this [collection](../README.md).

### Manual install

1. Download `plugin.ASCII_Tools.zip` from [GitHub Releases](https://github.com/scottdd/cudatext_plugins/releases).
2. Open the zip in CudaText (**File → Open**). CudaText offers to install it; confirm.
   The zip is flat (`install.inf` at the archive root). CudaText places that root in `py/cuda_asciitools/`. If you unzip by hand, extract into `py/cuda_asciitools/` so `install.inf` sits directly in that folder. Do not leave the files loose in `py/`, and do not add an extra nested folder.
3. Restart CudaText, or use **Plugins → Reload plugins**.

| Platform | `py` folder | Python |
|----------|-------------|--------|
| Windows | `<folder containing cudatext.exe>\py\` (Windows builds are portable; this is **not** `%APPDATA%`) | Bundled with CudaText |
| macOS | `~/Library/Application Support/CudaText/py/` | Install Python 3 |
| Linux | `~/.config/cudatext/py/` (or `$XDG_CONFIG_HOME/cudatext/py/`) | Install Python 3 |
| Portable (.xz archives, any exe next to a `data/` folder) | `<CudaText exe folder>/py/` | Same as platform |

On macOS and Linux, CudaText needs a system Python 3 to run plugins. Windows builds include it.

### Updating from Tab Menu 0.6.3

Tab Menu 0.7.0 and later do not include these commands. After Tab Menu upgrades, install ASCII Tools from the same user channel. `Alt+F3` and `Alt+Shift+F3` belong to this plugin.

## Changelog

[readme/history.txt](readme/history.txt) and [GitHub Releases](https://github.com/scottdd/cudatext_plugins/releases).

## License

Plugin source: [Mozilla Public License 2.0](LICENSE).

The transliteration data is [AnyAscii](https://github.com/anyascii/anyascii), ISC License. See [anyascii/LICENSE](anyascii/LICENSE).

## For developers

For building, testing, and releasing, see [DEVELOPERS.md](DEVELOPERS.md).
