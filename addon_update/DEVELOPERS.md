# Developing Addons Update

Shared layout, tests, CI, packaging, and `./release.sh` are in [../DEVELOPERS.md](../DEVELOPERS.md). Everyday use is in [README.md](README.md).

## Module

- Install folder and Python package: `cuda_addon_update` (`subdir=` in `install.inf`).
- Repo directory: `addon_update`.
- Version **0.1.1** is `version=` in `install.inf` and `__version__` in `__init__.py` and `logic.py`.
- Zip: `dist/plugin.Addons_Update.zip` (`release.json`).
- Release tag: `addon_update-vX.Y.Z` (`./release.sh addon_update`).

Development symlink:

```bash
ln -sfn ~/Projects/cudatext_plugins/addon_update ~/.config/cudatext/py/cuda_addon_update
```

Tests, from the repo root:

```bash
python3 -m unittest discover -s addon_update/tests -t addon_update
```

`./pack.sh` in this directory writes the zip. `logic.py` has no CudaText imports.

Do not point Addon Manager **Install from GitHub** at this repository’s root URL. The repository name does not match `subdir=cuda_addon_update`.

## What the check does

`on_start` reads `settings/cuda_addon_update.json` (`APP_DIR_SETTINGS`). With `enabled` and `check_on_startup`, it schedules one-shot timer `cuda_addon_update.on_startup_delay` for `startup_delay_sec`. It also starts repeating timer `cuda_addon_update.on_timer` every `poll_minutes` (at least 60 seconds). The repeating timer calls `interval_elapsed` against `last_check_unix` and `interval_hours`; it does not itself mean “update every poll.”

`merge_config` fills `DEFAULT_CONFIG` and ignores keys whose names end in `_Hint`. It clamps `interval_hours` to at least 0.25, `startup_delay_sec` to at least 0, and `poll_minutes` to at least 1. Saving the config (`config_with_hints`) writes a `<key>_Hint` string beside each value. `last_check_unix` and `last_result` are maintained by the plugin.

Channel lists and `packages.ini` versions come from the built-in Addons Manager (`cuda_addonman`). User channels, proxy, and HTTPS verification are read from `cuda_addonman.json` into `cuda_addonman.opt`. Default channels and user channels are both fetched. Downloads use `requests` (`_quiet_get_url`) with that proxy and verify flag, and they do not show Addon Manager’s Retry/Abort dialogs. A failure is printed to the Console.

Zip-installed plugins, linters, formatters, and tree helpers that `select_outdated` accepts are removed with `do_remove_dir` and installed with `file_open(path, options='/silent')`, then recorded with `do_save_version`. Version comparison is a plain string less-than, matching Addon Manager. A local version of `preinstalled`, and any module in `STD_MODULES`, is not replaced. Which kinds are eligible is `allowed_kinds` (`update_plugins`, `update_linters`, and the other `update_*` keys).

A plugin directory that contains `.git` is not on the zip list. When plugin updates are enabled, the check runs `git stash save` and then `git pull` in that directory, and skips `STD_MODULES`.

`Check now` forces a run. Overlapping runs are refused (`_busy`). `Reload config` re-reads the JSON and restarts the poll timer.
