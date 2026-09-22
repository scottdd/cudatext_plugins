Plugin for CudaText: Addon Update (cuda_addon_update)
Version 0.1.0
Author: Scott (https://github.com/scottdd)

Automatically checks installed CudaText add-ons against Addon Manager
channels and applies updates without the Update checklist dialog.

Behavior:
  - On editor start (after a short delay), then every N hours (default 12)
  - Zip-installed add-ons: download + silent install (same path as Addon Manager)
  - Git-cloned plugins: git stash save + git pull in the plugin folder
  - Skips preinstalled stock modules that Addon Manager treats as "preinstalled"

Menus:
  Plugins → Addon Update → Check now
  Plugins → Addon Update → Show last result
  Options → Settings-plugins → Addon Update → Config...

Config file: settings/cuda_addon_update.json
  enabled            (bool, default true)
  interval_hours     (number, default 12)
  check_on_startup   (bool, default true)
  startup_delay_sec  (number, default 45)
  notify             (bool, default true)  — msg_status summary
  notify_dialog      (bool, default false) — msg_box when something updated
  update_plugins     (bool, default true)
  update_linters     (bool, default true)
  update_formatters  (bool, default true)
  update_treehelpers (bool, default true)
  update_lexers      (bool, default false)
  update_themes      (bool, default false)
  update_translations(bool, default false)

Requires the built-in Addons Manager (cuda_addonman) for channel lists and
version bookkeeping (packages.ini). Network downloads for auto-update are
quiet (no Retry/Abort dialogs); failures are logged to the console.

Install: open plugin.Addon_Update.zip in CudaText, or:
  ln -sfn ~/Projects/cudatext_plugins/addon_update ~/.config/cudatext/py/cuda_addon_update

Homepage: https://github.com/scottdd/cudatext_plugins/tree/main/addon_update
License: MPL 2.0
