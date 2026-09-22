Plugin for CudaText: Addons Update (cuda_addon_update)
Version 0.1.1
Author: Scott (https://github.com/scottdd)

Automatically checks installed CudaText add-ons against Addon Manager
channels and applies updates without the Update checklist dialog.

Behavior:
  - On editor start (after a short delay), then every N hours (default 12)
  - Zip-installed add-ons: download + silent install (same path as Addon Manager)
  - Git-cloned plugins: git stash save + git pull in the plugin folder
  - Skips preinstalled stock modules that Addon Manager treats as "preinstalled"

Menus:
  Plugins → Addons Update → Check now
  Plugins → Addons Update → Show last result
  Plugins → Addons Update → Reload config
  Options → Settings-plugins → Addons Update → Config...

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

Install on any machine (pick one):
  1) Open plugin.Addons_Update.zip in CudaText (File → Open) and confirm install.
     The zip is FLAT (install.inf at zip root). Do not wrap it in an extra folder.
  2) Addon Manager user channel:
     https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json
     Then install "Addons Update" from that channel.
  3) Dev symlink (this monorepo only):
     ln -sfn ~/Projects/cudatext_plugins/addon_update ~/.config/cudatext/py/cuda_addon_update

Do NOT use Addon Manager "Install from GitHub" on the monorepo root URL — the
repo name does not match subdir=cuda_addon_update (same limitation as Tab Menu).

After install, restart CudaText or use Plugins → Reload plugins. Target folder
must be py/cuda_addon_update/ (underscore), matching install.inf subdir=.

Homepage: https://github.com/scottdd/cudatext_plugins/tree/main/addon_update
License: MPL 2.0
