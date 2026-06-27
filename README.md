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

## Releases and updates

1. Build a plugin zip from its subdirectory: `./pack.sh` → `dist/plugin.Name.zip`
2. Attach zips to [GitHub Releases](https://github.com/scottdd/cudatext_plugins/releases) (zip name must be `kind.Name.zip`)
3. Update `addons/plugins.json` with the release URL and `"v"` version
4. Users add the raw channel URL in **Plugins → Addon Manager → Config → User channels**

## Adding another plugin

Create a new sibling directory (e.g. `cuda-my-plugin/`) with:

- `install.inf` (`subdir=cuda_my_plugin`, unique `title`)
- `__init__.py` with `class Command`
- `readme/readme.txt`, `readme/history.txt`
- `pack.sh` producing `dist/plugin.My_Plugin.zip`
- An entry in `addons/plugins.json`