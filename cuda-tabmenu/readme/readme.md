# Tab Menu (cuda_tabmenu)

CudaText plugin: tab context menu tools, Non-ASCII navigation and transliteration, and file info.

**Version:** 0.5  
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

### Search menu

The same **Non-ASCII** submenu is added under **Search** in the main menu bar. Commands apply to the **focused** editor.

### Hotkeys (defaults)

| Command | Default hotkey |
|---------|----------------|
| Tab Menu → Info | `Ctrl+Shift+Alt+I` |
| Tab Menu → Non-ASCII → Next | `Alt+F3` |
| Tab Menu → Non-ASCII → Previous | `Alt+Shift+F3` |

Hotkeys can be changed in **Options → Hotkeys**. Highlight, un-highlight, and transliterate are menu-only (no default hotkeys).

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
2. Host a channel JSON. The monorepo channel is [`addons/plugins.json`](../addons/plugins.json); per-plugin `addon-channel.json` is a copy template. Add the raw URL under **Plugins → Addon Manager → Config → User channels**.
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

## Third-party code

Transliteration uses a vendored copy of [AnyAscii](https://github.com/anyascii/anyascii) (ISC License) in `anyascii/`. Data files live in `anyascii/_data/`. No pip dependency is required.

## License

Plugin source: [Mozilla Public License 2.0](../LICENSE) (same family as [CudaText](https://github.com/Alexey-T/CudaText)).

Bundled AnyAscii data: ISC License — see [anyascii/LICENSE](../anyascii/LICENSE).