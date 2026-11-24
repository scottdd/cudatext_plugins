# Developing Tab Menu

Shared layout, tests, CI, packaging, and `./release.sh` are in [../DEVELOPERS.md](../DEVELOPERS.md). Everyday use is in [README.md](README.md).

## Module

- Install folder and Python package: `cuda_tabmenu` (`subdir=` in `install.inf`).
- Repo directory: `cuda-tabmenu`.
- Version **0.7.2** is `version=` in `install.inf` and `__version__` in `__init__.py` and `logic.py`.
- Zip: `dist/plugin.Tab_Menu.zip` (`release.json`).
- Release tag: `cuda-tabmenu-vX.Y.Z`.

Development symlink:

```bash
ln -sfn ~/Projects/cudatext_plugins/cuda-tabmenu ~/.config/cudatext/py/cuda_tabmenu
```

Tests, from the repo root:

```bash
python3 -m unittest discover -s cuda-tabmenu/tests -t cuda-tabmenu
```

`./pack.sh` in this directory writes the zip. `logic.py` has no CudaText imports. The 0.7.0 split removed Search-menu injection, `on_change_slow`, and the vendored AnyAscii package; those live in [ASCII Tools](../cuda-asciitools/DEVELOPERS.md).

## Commands and the tab popup

`install.inf` registers `on_start` and `on_tab_menu`. Plugins-menu captions and the File Info hotkey (`Ctrl+Shift+Alt+I`) come from `install.inf`. Methods on `Command` are what both the Plugins menu and the tab items call.

Tab items are added to the numeric popup id cached in `on_start`. Their tag prefix is `cuda_tabmenu_item_` (`TAG_PREFIX`). `on_tab_menu` deletes only those tags, then adds a separator and the nine items. Commands are bound to the `Command` instance (`command=self.menu_...`), and `self._tab_ed` is the editor passed to `on_tab_menu`. Plugins-menu handlers and hotkeys use the focused editor instead.

Hotkey text in the tab menu is a caption suffix, not `hotkey=`. See [Menus, hotkeys, and the tab popup](../DEVELOPERS.md#menus-hotkeys-and-the-tab-popup). Caching the numeric id before the first right-click is what lets ASCII Tools add its submenu beside these items. Resolving the string id `'tab'` again would rebuild the stock popup on older CudaText and drop both plugins’ items.

Items that need a path on disk pass `enabled=False` when `os.path.isfile` is false. Export to HTML is enabled only for a text document (`PROP_KIND == 'text'`).

| Action | Implementation |
|--------|----------------|
| Reveal, Open Folder, Open Terminal | `reveal_attempts`, `open_folder_attempts`, `terminal_attempts` in `logic.py`, then the first working launch for `PROC_GET_OS_SUFFIX` |
| Reopen | `cmd_FileReopen` on the clicked editor |
| Save a Copy As | `safe_write_bytes` of the buffer to the chosen path; the open tab’s filename and modified flag stay as they were |
| Duplicate | `suggest_duplicate_name` (`stem_copy.ext`, then `stem_copy2.ext`, …). Unmodified files use `safe_copy_file` (byte copy). Modified buffers use `safe_write_bytes` |
| Close and Delete | Confirm with the full path, `cmd_FileClose`, then `safe_delete_file` (unlinks; no trash) |
| Export to HTML | `cmd_FileExportHtml` on the clicked text tab |

Stock tab commands (close variants, rename, save, copy path, move group, pinned, tab color) are intentionally absent. `menu_proc('tab', ...)` appears once, inside the startup resolve.

Failures are `print`ed to the Console (`_log_error`) and a short status message is shown.

## File Info theme

The dialog is built by `build_file_info_dialog` from a `PROC_THEME_UI_DICT_GET` dict (`_ui_theme_dict`). `resolve_ui_palette` reads background and text keys. A missing, empty, or partial theme falls back to a light neutral palette, because CudaText’s built-in UI theme is light. Returned colors are TColors (`0xBBGGRR`). Status pills use `file_info_status_colors`.

Buttons are `button_ex` so they paint with the UI theme. `button_ex_label` strips `&`: ATButton draws the raw caption, and a literal ampersand would show. The host focuses Close, turns on key preview so Escape reaches the form, and scales with `DLG_SCALE`. Escape with no modifiers closes. Enter is left to the focused button. Ctrl+C is not claimed, so the path field can copy its selection. **Copy Info** copies `format_file_info` text, the same plain-text summary the dialog shows.
