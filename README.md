# cudatext_plugins

Monorepo of independent [CudaText](https://cudatext.github.io/) plugins by [scottdd](https://github.com/scottdd).

Each subdirectory is a standalone plugin with its own `install.inf`, `pack.sh`, and `readme/`.

## Plugins

| Directory | Module (`py/…`) | Description |
|-----------|-----------------|-------------|
| [cuda-tabmenu](cuda-tabmenu/) | `cuda_tabmenu` | Tab menu: Info, Open Path, Non-ASCII tools |

## Development install

Clone this repo, then symlink a plugin folder into CudaText's `py` directory. The install folder name uses an **underscore** (`subdir=` in `install.inf`), while repo folders use a **hyphen**:

```bash
ln -sfn ~/Projects/cudatext_plugins/cuda-tabmenu ~/.config/cudatext/py/cuda_tabmenu
```

Restart CudaText or use **Plugins → Reload plugins**.

**Note:** Addon Manager **Install from GitHub** only works when the repository root name matches `install.inf` `subdir=`. For this monorepo, use zip install, a channel URL, or a symlink — not the monorepo root URL.

## Tests

```bash
python3 -m unittest discover -s cuda-tabmenu/tests -t cuda-tabmenu
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
