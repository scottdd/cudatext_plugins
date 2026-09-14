# Tab Menu (cuda_tabmenu)

CudaText plugin: tab context menu tools, Non-ASCII navigation and transliteration, and file info.

**Version:** 0.6.1  
**Author:** Scott ([scottdd](https://github.com/scottdd))  
**Repository:** [scottdd/cudatext_plugins — cuda-tabmenu](https://github.com/scottdd/cudatext_plugins/tree/main/cuda-tabmenu)

## Features

### Tab right-click menu

- **Info** — dialog with file path, name, status (unsaved / saved / modified), encoding, lexer, sizes, and line/word counts (text documents).
- **Open Path** — open the containing folder in the system file manager (disabled for unsaved tabs).
- **Non-ASCII** submenu:
  - Highlight / Un-highlight Non-ASCII characters (code points above 127)
  - Next / Previous Non-ASCII character (moves caret and selects the character)
  - Transliterate to ASCII (whole document; asks for confirmation)

Highlight markers are refreshed after edits (on CudaText’s delayed change event). Transliterate keeps highlighting if it was on.

Next / Previous wrap at the document edge when Find’s **Wrapped search** option (O) is on — the same toggle used by F3 / Shift+F3. Status bar shows `Wrapped search` when a search crosses the edge.

### Search menu and Plugins menu

The same **Non-ASCII** commands appear under **Search** (focused editor) and **Plugins → Tab Menu**.

### Hotkeys (defaults)

| Command | Default hotkey |
|---------|----------------|
| Tab Menu → Info | `Ctrl+Shift+Alt+I` |
| Tab Menu → Non-ASCII → Next | `Alt+F3` |
| Tab Menu → Non-ASCII → Previous | `Alt+Shift+F3` |

Highlight, un-highlight, and transliterate have no default hotkeys; they can be bound in **Options → Hotkeys**.

`Alt+F3` / `Alt+Shift+F3` mirror CudaText’s find navigation (`F3` / `Shift+F3`).

## Installation

### Zip install (recommended)

1. Download `plugin.Tab_Menu.zip` from [Releases](https://github.com/scottdd/cudatext_plugins/releases) or build it locally (see below).
2. In CudaText: **Plugins → Addon Manager → Install**, choose the zip file  
   — or open the zip in CudaText (**File → Open file**).
3. Restart CudaText or use **Plugins → Reload plugins**.

### Updates (Addon Manager)

Addon Manager **Update** compares the version in its channel list (`v`) with the version recorded when you installed from that channel URL (in `settings/packages.ini`). It does **not** read `version=` from `install.inf`.

To receive updates:

1. Publish each release as `plugin.Tab_Menu.zip` on GitHub (name must be `kind.Name.zip` for channel parsing).
2. Host a channel JSON. The monorepo channel is [`addons/scottdd-plugins.json`](../addons/scottdd-plugins.json); per-plugin `addon-channel.json` is a copy template. Add the raw URL under **Plugins → Addon Manager → Config → User channels**.
3. Install (or update) via **Addon Manager → Install** from that channel, not only by opening a local zip. Opening a zip manually installs the plugin but does not register a version for Update.

Git clone / symlink installs show as **Git** in Update and are not version-checked.

Version strings are compared as plain text (`0.5` &lt; `0.6` works; prefer `0.6` over `0.10`, or use zero-padded forms like `0.05`).

### Manual install

Copy the `cuda_tabmenu` folder into the CudaText `py` directory:

- Linux: `~/.config/cudatext/py/cuda_tabmenu/`
- Windows: `%APPDATA%\cudatext\py\cuda_tabmenu\`
- macOS: `~/Library/Application Support/cudatext/py/cuda_tabmenu/`

The folder must contain `install.inf` and `__init__.py` at its root.

### From this monorepo

If you clone [cudatext_plugins](https://github.com/scottdd/cudatext_plugins), symlink or copy `cuda-tabmenu/` to `py/cuda_tabmenu/` (note: install folder name uses an underscore).

## Building the zip

From this directory:

```bash
./pack.sh
```

Output: `dist/plugin.Tab_Menu.zip`

## Tests

From the monorepo root:

```bash
python3 -m unittest discover -s cuda-tabmenu/tests -t cuda-tabmenu
python3 -m unittest discover -s scripts -t scripts
```

## Releasing

From the monorepo root (after bumping version in `install.inf`, `__init__.py`, and `readme/history.txt`):

```bash
./release.sh cuda-tabmenu
```

This packs the zip, updates `addons/scottdd-plugins.json`, pushes, and publishes a GitHub release.

## Third-party code

Transliteration uses a vendored copy of [AnyAscii](https://github.com/anyascii/anyascii) (ISC License) in `anyascii/`. Data files live in `anyascii/_data/`. No pip dependency is required.

## License

Plugin source: [Mozilla Public License 2.0](../LICENSE) (same family as [CudaText](https://github.com/Alexey-T/CudaText)).

Bundled AnyAscii data: ISC License — see [anyascii/LICENSE](../anyascii/LICENSE).
