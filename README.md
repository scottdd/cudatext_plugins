# cudatext_plugins

Independent [CudaText](https://cudatext.github.io/) plugins by [scottdd](https://github.com/scottdd).

## 🚀 Quick install (one line!)

> [!TIP]
> **Get every plugin here in CudaText's Addon Manager by adding one URL:**
>
> 1. In CudaText open **Plugins → Addon Manager → Config**.
> 2. In **User channels**, add this line:
>
>    ```
>    https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json
>    ```
>
> 3. Click OK, then **Plugins → Addon Manager → Install** and pick the plugins you want. ✅

> [!WARNING]
> ⚠️ **Only add channels you trust.** Adding a user channel lets CudaText download and run Python code from this repository with **your user permissions**. Future updates also come from this channel. The code is provided **as-is, with no warranty** ([MPL-2.0](https://www.mozilla.org/MPL/2.0/)). Please review the [source](https://github.com/scottdd/cudatext_plugins) and [releases](https://github.com/scottdd/cudatext_plugins/releases) before installing.

### 📦 Manual install (no channel)

1. Download `plugin.<Name>.zip` from [GitHub Releases](https://github.com/scottdd/cudatext_plugins/releases).
2. Either open the zip in CudaText (**File → Open**) and confirm the installer prompt, **or** extract it into your CudaText `py` folder:

| Platform | `py` folder | Python |
|----------|-------------|--------|
| 🪟 Windows | `%AppData%\CudaText\py\` | Bundled with CudaText |
| 🍎 macOS | `~/Library/Application Support/CudaText/py/` | Install Python 3 |
| 🐧 Linux | `~/.config/cudatext/py/` | Install Python 3 |
| 💼 Portable | `<CudaText exe folder>/py/` | Same as platform |

3. Restart CudaText.

> [!IMPORTANT]
> On macOS and Linux CudaText needs a system Python 3 to run plugins. Windows builds include it.

---

## Plugins

| Directory | Module (`py/…`) | Description |
|-----------|-----------------|-------------|
| [cuda-tabmenu](cuda-tabmenu/) | `cuda_tabmenu` | Tab menu: Info, Open Path, Non-ASCII tools |
| [addon_update](addon_update/) | `cuda_addon_update` | Addons Update: auto-update installed add-ons on startup / timer |

## 🛠️ For developers

Each subdirectory is a standalone plugin with its own `install.inf`, `pack.sh`, and `readme/`.

### Development install

Clone this repo, then symlink a plugin folder into CudaText's `py` directory. The install folder name uses an **underscore** (`subdir=` in `install.inf`), while repo folders use a **hyphen**:

```bash
ln -sfn ~/Projects/cudatext_plugins/cuda-tabmenu ~/.config/cudatext/py/cuda_tabmenu
ln -sfn ~/Projects/cudatext_plugins/addon_update ~/.config/cudatext/py/cuda_addon_update
```

Restart CudaText or use **Plugins → Reload plugins**.

**Note:** Addon Manager **Install from GitHub** only works when the repository root name matches `install.inf` `subdir=`. For this monorepo, use zip install, a channel URL, or a symlink — not the monorepo root URL.

## Tests

```bash
python3 -m unittest discover -s cuda-tabmenu/tests -t cuda-tabmenu
python3 -m unittest discover -s addon_update/tests -t addon_update
python3 -m unittest discover -s scripts -t scripts
```

## Releases and updates

Prerequisites: [GitHub CLI](https://cli.github.com/) logged in (`gh auth login`).

1. Bump `version=` in `install.inf`, `__version__` in `__init__.py`, and `readme/history.txt`
2. From the repo root, run:

```bash
./release.sh cuda-tabmenu
```

This will:

- run `cuda-tabmenu/pack.sh` → `dist/plugin.Name.zip`
- update `addons/scottdd-plugins.json` and the plugin's `addon-channel.json`
- commit and push those channel changes to `main`
- create (or update) a GitHub release tagged `cuda-tabmenu-vX.Y` with the zip attached

Dry run: `./release.sh cuda-tabmenu --dry-run`  
Skip git push: `--no-git`  
Skip GitHub upload: `--no-github`

Users add the raw channel URL in **Plugins → Addon Manager → Config → User channels**:

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
