# Developing cudatext_plugins

Notes for changing, testing, and releasing these plugins. Everyday install and use are in [README.md](README.md).

## Repository layout

Each plugin is a sibling directory with its own `install.inf`, `__init__.py`, `logic.py`, `pack.sh`, `release.json`, `addon-channel.json`, and `readme/`.

| Directory | Install folder (`subdir=`) | Zip |
|-----------|----------------------------|-----|
| `cuda-asciitools` | `cuda_asciitools` | `plugin.ASCII_Tools.zip` |
| `cuda-tabmenu` | `cuda_tabmenu` | `plugin.Tab_Menu.zip` |
| `addon_update` | `cuda_addon_update` | `plugin.Addons_Update.zip` |

Repo directory names use a hyphen (`cuda-asciitools`, `cuda-tabmenu`) or, for Addons Update, the name `addon_update`. The folder CudaText imports is `subdir=` in `install.inf`, with underscores.

Shared files:

- `addons/scottdd-plugins.json` is the user channel (a JSON array of published plugins).
- `release.sh` calls `scripts/release_plugin.py`.
- `.github/workflows/tests.yml` runs the unit tests.

Plugin notes:

- [ASCII Tools](cuda-asciitools/DEVELOPERS.md)
- [Tab Menu](cuda-tabmenu/DEVELOPERS.md)
- [Addons Update](addon_update/DEVELOPERS.md)

## Development install

Clone this repo, then symlink a plugin folder into CudaText’s `py` directory. The link name is the underscore form:

```bash
ln -sfn ~/Projects/cudatext_plugins/cuda-asciitools ~/.config/cudatext/py/cuda_asciitools
ln -sfn ~/Projects/cudatext_plugins/cuda-tabmenu ~/.config/cudatext/py/cuda_tabmenu
ln -sfn ~/Projects/cudatext_plugins/addon_update ~/.config/cudatext/py/cuda_addon_update
```

Restart CudaText or use **Plugins → Reload plugins**.

**Install from GitHub** in Addon Manager only works when the repository root name matches `install.inf` `subdir=`. The root here is `cudatext_plugins`, so that menu item does not install these plugins. Use a zip, the user channel, or a symlink.

## Tests

From the repo root:

```bash
python3 -m unittest discover -s cuda-asciitools/tests -t cuda-asciitools
python3 -m unittest discover -s cuda-tabmenu/tests -t cuda-tabmenu
python3 -m unittest discover -s addon_update/tests -t addon_update
python3 -m unittest discover -s scripts -t scripts
```

`logic.py` in each plugin avoids CudaText imports so those tests run outside the editor. The `scripts` suite covers `scripts/release_plugin.py`.

## Continuous integration

[`.github/workflows/tests.yml`](.github/workflows/tests.yml) runs the four commands above on Ubuntu with Python 3.12. It runs on push and pull request to `main`.

## Releases

Prerequisite: [GitHub CLI](https://cli.github.com/) logged in (`gh auth login`).

1. Bump `version=` in `install.inf` and `__version__` in `__init__.py` and `logic.py`.
2. Add a newest-first block at the top of `readme/history.txt`, starting with `X.Y.Z (YYYY-MM-DD)`.
3. From the repo root:

```bash
./release.sh cuda-asciitools
./release.sh cuda-tabmenu
./release.sh addon_update
```

`./release.sh <plugin>` runs `scripts/release_plugin.py`. For directory `<plugin>` at version `X.Y.Z` it:

- runs `<plugin>/pack.sh`, which writes `dist/<zip>`
- builds the GitHub release download URL for tag `<plugin>-vX.Y.Z` and that zip name
- updates `addons/scottdd-plugins.json` and `<plugin>/addon-channel.json` with `url`, `desc` (from `install.inf`), `module` (`subdir=`), and `v`
- commits `addons/scottdd-plugins.json`, `addon-channel.json`, `install.inf`, `__init__.py`, and `readme/history.txt`, then pushes to `main`
- creates or updates the GitHub release tagged `<plugin>-vX.Y.Z`, titled `<Title> X.Y.Z`, with the zip attached

Release notes default to the newest version block in `readme/history.txt` (`notes_from_history`). A history that does not start with a version header falls back to the first 8 lines. Pass `--notes` with text, or a path to a file, to override that.

Leave the channel URL unset until the zip is actually uploaded. The script writes the URL when it publishes the release.

The channel filename must stay `scottdd-plugins.json`. Addon Manager caches channels by basename, and CudaText’s official channel is already `plugins.json`.

Users add this raw URL under **Options → Settings-plugins → Addons Manager → Config... → User channels:**

`https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json`

### Options

- `./release.sh cuda-asciitools --dry-run` prints the actions and does not change git, the channel files, or GitHub.
- `--no-git` skips the commit and the push.
- `--no-github` skips the release upload.
- An existing tag is updated (`gh release edit` plus `gh release upload --clobber`) instead of failing.

### GitHub Latest badge

Releases are per plugin. GitHub’s Latest badge is the single release published most recently, so it is a poor pointer at “current everything.” Install from the user channel, or from the tag `<plugin>-vX.Y.Z`. A commit on `main` is not what the channel serves until that plugin is released and `addons/scottdd-plugins.json` is updated.

## Packaging

Each `pack.sh` builds a **flat** zip: `install.inf` and `__init__.py` at the archive root. Addon Manager copies that root into `py/<subdir>/`. An extra `<subdir>/` directory inside the zip installs as `py/<subdir>/<subdir>/`. Python then imports an empty package and `Command` never runs.

The rsync exclude list omits `__pycache__`, `*.pyc`, `.git`, `dist/`, `pack.sh`, `addon-channel.json`, `release.json`, `tests/`, and `DEVELOPERS.md`. `readme/readme.txt` is the text CudaText shows for the addon. `README.md` is the same user guide in Markdown and is still packed. `readme/history.txt` is packed and is left as the changelog.

## Menus, hotkeys, and the tab popup

ASCII Tools and Tab Menu both add items to CudaText’s tab popup, and both show the hotkey currently assigned to the Plugins command.

Do not pass `hotkey=` to `menu_proc` for those items. `hotkey=` is stored on `TMenuItem.ShortCut` through `TextToShortCutRaw` (one stroke plus modifiers). The Plugins menu item already owns that shortcut, from `GetShortcutFromCommand` (Keys1 only, and only when it is a single stroke). A second `ShortCut` for the same stroke is unsafe:

- On Qt, `QAction.setShortcut` is a window shortcut even for a popup item. A second action with the same key is ambiguous, and Qt fires neither.
- On Win32 and GTK the main menu consumes the first matching shortcut. Search is walked before Plugins, so a second shortcut can steal the key onto the Search item.

`caption_with_hotkey` appends a tab and the primary stroke (`caption + '\t' + stroke`) from `PROC_GET_HOTKEY` (`Keys1|Keys2`). The text after the tab is display-only: Win32 and Qt draw it in the shortcut column and do not register another accelerator. Chords (strokes joined with `*`) are shown that way because `ShortCut` cannot hold them. `shortcut_for_menu` returns a value `TextToShortCutRaw` would accept, or `''`; callers that mirror a Plugins command still omit `hotkey=`. A missing `PROC_GET_HOTKEY` degrades to no suffix. Pressing the key still runs the Plugins command once, on the focused editor.

The string id `'tab'` calls `InitPopupTab`. Resolve it once during `on_start` with `menu_proc('tab', MENU_GET_PROP)`, keep the numeric id (`tab_handle_from_prop` / `usable_menu_handle`), and add items to that id. Calling the string id again inside `on_tab_menu`, after another plugin has added items, rebuilds the stock popup on older CudaText and drops those items. Current builds create the popup only while it is nil; caching still keeps both plugins off the string id once items exist. Each plugin deletes only items whose tag has its own prefix, then adds them again, so the two submenus can share the popup.

`print()` is what the CudaText Console shows. `traceback.print_exc()` goes to stderr, which the Console does not show. Both plugins log with `print` and flush stdout.

## Adding another plugin

Create a sibling directory (for example `cuda-my-plugin/`) with:

- `install.inf` (`subdir=cuda_my_plugin`, a unique `title`)
- `__init__.py` with `class Command`
- `readme/readme.txt` and `readme/history.txt`
- `pack.sh` writing `dist/plugin.My_Plugin.zip` (Addon Manager parses `kind.Name.zip` from the URL)
- `release.json` with that zip file name (see `cuda-tabmenu/release.json`)

`./release.sh cuda-my-plugin` tags `cuda-my-plugin-vX.Y.Z` and adds the channel entry. The zip name has to match `release.json`.
