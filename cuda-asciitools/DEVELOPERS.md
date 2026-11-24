# Developing ASCII Tools

Shared layout, tests, CI, packaging, and `./release.sh` are in [../DEVELOPERS.md](../DEVELOPERS.md). Everyday use is in [README.md](README.md).

## Module

- Install folder and Python package: `cuda_asciitools` (`subdir=` in `install.inf`).
- Repo directory: `cuda-asciitools`.
- Version **0.2.0** is `version=` in `install.inf` and `__version__` in `__init__.py` and `logic.py`.
- Zip: `dist/plugin.ASCII_Tools.zip` (`release.json`).
- Release tag: `cuda-asciitools-vX.Y.Z`.

Development symlink:

```bash
ln -sfn ~/Projects/cudatext_plugins/cuda-asciitools ~/.config/cudatext/py/cuda_asciitools
```

Tests, from the repo root:

```bash
python3 -m unittest discover -s cuda-asciitools/tests -t cuda-asciitools
```

`./pack.sh` in this directory writes the zip. `logic.py` has no CudaText imports.

## Commands and events

`install.inf` registers `on_start`, `on_change_slow`, `on_init_plugins_menu`, `on_tab_menu`, `on_focus`, and `on_state`.

Plugins menu captions and the two default hotkeys (`Alt+F3`, `Alt+Shift+F3`) come from `install.inf`. Methods live on `Command` in `__init__.py`.

| Surface | When it is built | Tag |
|---------|------------------|-----|
| **Search → ASCII Tools** | `on_init_plugins_menu`, parent on `top-sr` | `cuda_asciitools_search` (`SEARCH_MENU_TAG`) |
| Tab submenu | `on_tab_menu` | prefix `cuda_asciitools_tab_` (`TAB_TAG_PREFIX`) |

The tab submenu runs on the editor passed to `on_tab_menu`. Plugins, Search, the Command Palette, and the hotkey call the same methods with the focused editor. A non-text editor disables the submenu.

Hotkey text in Search and in the tab submenu is a caption suffix, not `hotkey=`. See [Menus, hotkeys, and the tab popup](../DEVELOPERS.md#menus-hotkeys-and-the-tab-popup). The numeric tab-popup id is cached in `on_start` so this submenu can sit beside Tab Menu. This plugin removes only `cuda_asciitools_tab_` items before adding them again.

Highlight marks use tag `88021` (`NONASCII_MARK_TAG`). `on_change_slow` redraws them while that editor is in the highlighted set. A successful transliterate, strip, or normalize calls the same redraw when highlighting was already on.

Whole-document and selection edits go through `editor.replace`, so Undo still applies. Read-only editors are refused before that call. The list report’s **Open in Tab** path is separate: it opens a scratch tab and uses `set_text_all` there.

Next / Previous read Find’s wrapped-search flag with `PROC_GET_FINDER_PROP` (`finder_wrap_enabled`). A wrap sets the status bar to `Wrapped search`.

Transliteration calls the vendored [AnyAscii](https://github.com/anyascii/anyascii) package in `anyascii/` (`from .anyascii import anyascii`). There is no pip dependency. Its data is ISC; see `anyascii/LICENSE`.

Failures are `print`ed to the Console (`_log_error`) and a short status message is shown.
