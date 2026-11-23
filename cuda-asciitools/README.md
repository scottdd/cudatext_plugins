# ASCII Tools (cuda_asciitools)

CudaText plugin that finds non-ASCII characters and converts the punctuation you usually want as plain ASCII. Accented letters stay unless you ask to transliterate or strip them.

**Version:** 0.1.0
**Author:** Scott ([scottdd](https://github.com/scottdd))

These commands moved out of **Tab Menu** in 0.7.0. Install **ASCII Tools** if you still want them (including `Alt+F3` / `Alt+Shift+F3`).

## Quick install

1. In CudaText open **Options → Settings-plugins → Addons Manager → Config...**
2. In **User channels:** add:

   ```
   https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json
   ```

3. Click OK, then **Plugins → Addons Manager → Install...** and choose **ASCII Tools**.

> [!WARNING]
> **Only add channels you trust.** A user channel lets CudaText download and run Python from this repository with **your user permissions**. Later updates come from the same channel. The code is provided **as-is, with no warranty** ([MPL-2.0](https://www.mozilla.org/MPL/2.0/)). Please review the [source](https://github.com/scottdd/cudatext_plugins) and [releases](https://github.com/scottdd/cudatext_plugins/releases) before installing.

The channel lists **published** releases. A version shows up there after it is released, not merely because it is on `main`.

## Commands

The same items are under **Plugins → ASCII Tools** and **Search → ASCII Tools** (the Search entry is added when plugins load; its tag is `cuda_asciitools_search`).

| Command | What it does |
|---------|----------------|
| Highlight Non-ASCII | Marks code points above 127. While this is on, edits refresh the marks. |
| Un-highlight Non-ASCII | Clears those marks. |
| Next Non-ASCII Character | `Alt+F3`. Selects the next match. Wraps when Find’s **Wrapped search** (O) is on. |
| Previous Non-ASCII Character | `Alt+Shift+F3`. Same wrap rule, searching backward. |
| List Non-ASCII Characters | Line, column (1-based), character, `U+XXXX`, and Unicode name, plus a count. Uses the selection when there is one, otherwise the whole document. **Copy** copies the report. **Open in Tab** puts it in a new scratch tab. |
| Transliterate to ASCII | AnyAscii. Selection in place; otherwise asks, then converts the whole document. |
| Strip Non-ASCII Characters | Deletes code points above 127. Same selection / confirm rules. |
| Normalize Punctuation & Spaces to ASCII | Smart quotes, primes, dashes, minus, ellipsis, unusual spaces, and list bullets become ASCII. Zero-width spaces are removed. Accented letters are kept. |

Highlighting is drawn again after a successful transliterate, strip, or normalize when it was already on. Whole-document edits go through the editor replace API so Undo still works. Read-only documents are not modified.

Next / Previous show `Wrapped search` on the status bar when they cross the edge of the document.

## Manual install

1. Download `plugin.ASCII_Tools.zip` from [Releases](https://github.com/scottdd/cudatext_plugins/releases), or run `./pack.sh` in this directory (`dist/plugin.ASCII_Tools.zip`).
2. In CudaText choose **File → Open**, open the zip, and confirm the install.
3. Restart CudaText, or use **Plugins → Reload plugins**.

The zip is **flat**: `install.inf` is at the root of the archive. CudaText’s installer places that root into `py/cuda_asciitools/`. If you unzip yourself, extract into `py/cuda_asciitools/` so `install.inf` is directly inside it. Do not add another nested folder, and do not dump the files into `py/` itself.

| Platform | `py` folder | Python |
|----------|-------------|--------|
| Windows | `<folder containing cudatext.exe>\py\` (Windows builds are portable; this is **not** `%APPDATA%`) | Bundled with CudaText |
| macOS | `~/Library/Application Support/CudaText/py/` | Install Python 3 |
| Linux | `~/.config/cudatext/py/` (or `$XDG_CONFIG_HOME/cudatext/py/`) | Install Python 3 |
| Portable (.xz archives, any exe next to a `data/` folder) | `<CudaText exe folder>/py/` | Same as the platform |

### From this monorepo

```bash
ln -sfn ~/Projects/cudatext_plugins/cuda-asciitools ~/.config/cudatext/py/cuda_asciitools
```

The repo folder uses a hyphen. The install folder (`subdir=` in `install.inf`) uses an underscore.

Addon Manager **Install from GitHub** only works when the repository root name matches `subdir=`. For this monorepo, use the zip, the user channel, or a symlink.

## Tests

From the monorepo root:

```bash
python3 -m unittest discover -s cuda-asciitools/tests -t cuda-asciitools
```

## Third-party code

Transliteration uses a vendored copy of [AnyAscii](https://github.com/anyascii/anyascii) (ISC License) in `anyascii/`. No pip dependency is required.

## License

Plugin source: [Mozilla Public License 2.0](LICENSE).

Bundled AnyAscii data: ISC License — see [anyascii/LICENSE](anyascii/LICENSE).
