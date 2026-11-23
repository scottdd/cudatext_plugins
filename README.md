# cudatext_plugins

Independent [CudaText](https://cudatext.github.io/) plugins by [scottdd](https://github.com/scottdd).

## Quick install

> [!TIP]
> **Get every published plugin here in CudaText's Addon Manager by adding one URL:**
>
> 1. In CudaText open **Options → Settings-plugins → Addons Manager → Config...**
> 2. In the **User channels:** box, add this line:
>
>    ```
>    https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json
>    ```
>
> 3. Click OK, then **Plugins → Addons Manager → Install...** and pick the plugins you want.

> [!WARNING]
> **Only add channels you trust.** Adding a user channel lets CudaText download and run Python code from this repository with **your user permissions**. Future updates also come from this channel. The code is provided **as-is, with no warranty** ([MPL-2.0](https://www.mozilla.org/MPL/2.0/)). Please review the [source](https://github.com/scottdd/cudatext_plugins) and [releases](https://github.com/scottdd/cudatext_plugins/releases) before installing.

The channel file lists **published** release zips. A change on `main` is not installed until that plugin is released and the channel file is updated.

### Manual install (no channel)

1. Download `plugin.<Name>.zip` from [GitHub Releases](https://github.com/scottdd/cudatext_plugins/releases).
2. Open the zip in CudaText (**File → Open**). CudaText offers to install it; confirm.
   The zips are flat (`install.inf` at the archive root). If you unzip by hand, extract into `py/<module>/` from the table below so `install.inf` sits directly in that folder. Do not leave the files loose in `py/`, and do not add an extra nested folder.
3. Restart CudaText.

| Platform | `py` folder | Python |
|----------|-------------|--------|
| Windows | `<folder containing cudatext.exe>\py\` (Windows builds are portable; this is **not** `%APPDATA%`) | Bundled with CudaText |
| macOS | `~/Library/Application Support/CudaText/py/` | Install Python 3 |
| Linux | `~/.config/cudatext/py/` (or `$XDG_CONFIG_HOME/cudatext/py/`) | Install Python 3 |
| Portable (.xz archives, any exe next to a `data/` folder) | `<CudaText exe folder>/py/` | Same as platform |

On macOS and Linux, CudaText needs a system Python 3 to run plugins. Windows builds include it.

## Plugins

| Directory | Module (`py/…`) | Description |
|-----------|-----------------|-------------|
| [cuda-asciitools](cuda-asciitools/) | `cuda_asciitools` | ASCII Tools: highlight, find, list, strip, normalize, and transliterate non-ASCII text |
| [cuda-tabmenu](cuda-tabmenu/) | `cuda_tabmenu` | Tab Menu: tab right-click actions (file info, reveal, folder, terminal, reload, copy, duplicate, delete, export HTML) |
| [addon_update](addon_update/) | `cuda_addon_update` | Addons Update: auto-update installed add-ons on startup / timer |

### Tab Menu 0.6.3 → 0.7.0

Tab Menu **0.7.0** is file actions only. Non-ASCII tools (highlight, next/previous on `Alt+F3` / `Alt+Shift+F3`, transliterate, and the newer list / strip / normalize commands) live in **ASCII Tools**.

`0.7.0` sorts after `0.6.3`, so Addon Manager can upgrade an existing Tab Menu install once that release is on the channel. After upgrading, install **ASCII Tools** from the same user channel if you still want the character tools.

## For developers

Each subdirectory is a standalone plugin with its own `install.inf`, `pack.sh`, and `readme/`.

### Development install

Clone this repo, then symlink a plugin folder into CudaText's `py` directory. The install folder name uses an **underscore** (`subdir=` in `install.inf`), while repo folders use a **hyphen**:

```bash
ln -sfn ~/Projects/cudatext_plugins/cuda-asciitools ~/.config/cudatext/py/cuda_asciitools
ln -sfn ~/Projects/cudatext_plugins/cuda-tabmenu ~/.config/cudatext/py/cuda_tabmenu
ln -sfn ~/Projects/cudatext_plugins/addon_update ~/.config/cudatext/py/cuda_addon_update
```

Restart CudaText or use **Plugins → Reload plugins**.

**Note:** Addon Manager **Install from GitHub** only works when the repository root name matches `install.inf` `subdir=`. For this monorepo, use zip install, a channel URL, or a symlink — not the monorepo root URL.

## Tests

```bash
python3 -m unittest discover -s cuda-asciitools/tests -t cuda-asciitools
python3 -m unittest discover -s cuda-tabmenu/tests -t cuda-tabmenu
python3 -m unittest discover -s addon_update/tests -t addon_update
python3 -m unittest discover -s scripts -t scripts
```

## Releases and updates

Prerequisites: [GitHub CLI](https://cli.github.com/) logged in (`gh auth login`).

1. Bump `version=` in `install.inf`, `__version__` in `__init__.py`, and `readme/history.txt`
2. From the repo root, run:

```bash
./release.sh cuda-asciitools
./release.sh cuda-tabmenu
```

This will:

- run that plugin's `pack.sh` → `dist/plugin.Name.zip`
- update `addons/scottdd-plugins.json` and the plugin's `addon-channel.json`
- commit and push those channel changes to `main`
- create (or update) a GitHub release tagged `<plugin>-vX.Y` with the zip attached

Do not point `addons/scottdd-plugins.json` at a zip that has not been uploaded. The release script writes the channel URL when it publishes the release.

Dry run: `./release.sh cuda-asciitools --dry-run`
Skip git push: `--no-git`
Skip GitHub upload: `--no-github`

Users add the raw channel URL in **Options → Settings-plugins → Addons Manager → Config... → User channels:**:

`https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json`

The filename must not be `plugins.json`: Addon Manager caches channels by basename, and CudaText’s official channel already uses that name.

## Adding another plugin

Create a new sibling directory (e.g. `cuda-my-plugin/`) with:

- `install.inf` (`subdir=cuda_my_plugin`, unique `title`)
- `__init__.py` with `class Command`
- `readme/readme.txt`, `readme/history.txt`
- `pack.sh` producing `dist/plugin.My_Plugin.zip`
- `release.json` with the zip file name (see `cuda-tabmenu/release.json`)
- An entry in `addons/scottdd-plugins.json` (the release script maintains this)
