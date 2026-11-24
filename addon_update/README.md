# Addons Update (cuda_addon_update)

CudaText plugin that checks installed add-ons against Addon Manager channels and applies updates without the Update checklist dialog.

**Version:** 0.1.1
**Author:** Scott ([scottdd](https://github.com/scottdd))

## Quick install

1. In CudaText open **Options → Settings-plugins → Addons Manager → Config...**
2. In **User channels:** add:

   ```
   https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json
   ```

3. Click OK, then **Plugins → Addons Manager → Install...** and choose **Addons Update**.

> [!WARNING]
> **Only add channels you trust.** A user channel lets CudaText download and run Python from this repository with **your user permissions**. Later updates come from the same channel. The code is provided **as-is, with no warranty** ([MPL-2.0](https://www.mozilla.org/MPL/2.0/)). Please review the [source](https://github.com/scottdd/cudatext_plugins) and [releases](https://github.com/scottdd/cudatext_plugins/releases) before installing.

This plugin itself installs from that channel. The channels it later updates *from* are whatever you have configured in Addon Manager, including this one.

## What it does

- On editor start (after a short delay), then every N hours (default 12).
- Zip-installed add-ons: download and silent install, the same path Addon Manager uses.
- Git-cloned plugins: `git stash save` and `git pull` in the plugin folder.
- Skips preinstalled stock modules that Addon Manager treats as preinstalled.

Menus:

- **Plugins → Addons Update → Check now**
- **Plugins → Addons Update → Show last result**
- **Plugins → Addons Update → Reload config**
- **Options → Settings-plugins → Addons Update → Config...**

Config file: `settings/cuda_addon_update.json`

| Key | Default | Meaning |
|-----|---------|---------|
| `enabled` | true | Master switch |
| `interval_hours` | 12 | Hours between checks |
| `check_on_startup` | true | Check after startup |
| `startup_delay_sec` | 45 | Delay before the first check |
| `poll_minutes` | 5 | How often the idle timer wakes to check whether the configured check interval has elapsed |
| `notify` | true | Status-bar summary |
| `notify_dialog` | false | Dialog when something updated |
| `update_plugins` | true | |
| `update_linters` | true | |
| `update_formatters` | true | |
| `update_treehelpers` | true | |
| `update_lexers` | false | |
| `update_themes` | false | |
| `update_translations` | false | |

It needs the built-in Addons Manager (`cuda_addonman`) for channel lists and `packages.ini`. Download failures are written to the Console; auto-update does not show Retry/Abort dialogs.

## Manual install

1. Download `plugin.Addons_Update.zip` from [Releases](https://github.com/scottdd/cudatext_plugins/releases), or run `./pack.sh` (`dist/plugin.Addons_Update.zip`).
2. In CudaText choose **File → Open**, open the zip, and confirm the install.
3. Restart CudaText, or use **Plugins → Reload plugins**.

The zip is **flat**: `install.inf` is at the root of the archive. Opening it installs into `py/cuda_addon_update/`. If you unzip yourself, extract into that folder so `install.inf` is directly inside it. Do not wrap the zip in an extra folder.

| Platform | `py` folder | Python |
|----------|-------------|--------|
| Windows | `<folder containing cudatext.exe>\py\` (Windows builds are portable; this is **not** `%APPDATA%`) | Bundled with CudaText |
| macOS | `~/Library/Application Support/CudaText/py/` | Install Python 3 |
| Linux | `~/.config/cudatext/py/` (or `$XDG_CONFIG_HOME/cudatext/py/`) | Install Python 3 |
| Portable (.xz archives, any exe next to a `data/` folder) | `<CudaText exe folder>/py/` | Same as the platform |

### From this monorepo

```bash
ln -sfn ~/Projects/cudatext_plugins/addon_update ~/.config/cudatext/py/cuda_addon_update
```

Do not use Addon Manager **Install from GitHub** on the monorepo root URL. The repository name does not match `subdir=cuda_addon_update`.

## Tests

From the monorepo root:

```bash
python3 -m unittest discover -s addon_update/tests -t addon_update
```

## License

[Mozilla Public License 2.0](LICENSE).
