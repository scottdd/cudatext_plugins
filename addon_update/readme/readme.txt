Plugin for CudaText: Addons Update (cuda_addon_update)
Version 0.1.1
Author: Scott (https://github.com/scottdd)

Automatically checks installed CudaText add-ons against Addon Manager
channels and applies updates without the Update checklist dialog.

QUICK INSTALL
  Options → Settings-plugins → Addons Manager → Config...
  User channels: add this line:

    https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json

  Then Plugins → Addons Manager → Install... and choose Addons Update.

TRUST
  Only add channels you trust. A user channel lets CudaText download and
  run Python from that repository with your user permissions. Future
  updates come from the same channel. The code is provided as-is, with
  no warranty (MPL-2.0). Please review the source and releases first:
    https://github.com/scottdd/cudatext_plugins

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
  poll_minutes       (number, default 5)   — how often the idle timer wakes to check whether the configured check interval has elapsed
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

MANUAL INSTALL
  1. Download plugin.Addons_Update.zip from GitHub Releases, or build it
     with ./pack.sh (output: dist/plugin.Addons_Update.zip).
  2. In CudaText choose File → Open, open the zip, and confirm install.
     The zip is FLAT (install.inf at the zip root). If you unzip by hand,
     put the files in py/cuda_addon_update/ so install.inf sits directly in
     that folder. Do not wrap the zip in an extra folder, and do not dump
     the files loose into py/.
  3. Restart CudaText, or use Plugins → Reload plugins.

  py folder (the install.inf "subdir" is cuda_addon_update):

    Windows   <folder containing cudatext.exe>\py\
              Windows builds are portable. This is NOT %APPDATA%.
    macOS     ~/Library/Application Support/CudaText/py/
    Linux     ~/.config/cudatext/py/
              or $XDG_CONFIG_HOME/cudatext/py/
    Portable  <CudaText exe folder>/py/
              (.xz archives, or any exe next to a data/ folder)

  macOS and Linux need a system Python 3. Windows builds include Python.

Dev symlink (this monorepo only):

  ln -sfn ~/Projects/cudatext_plugins/addon_update ~/.config/cudatext/py/cuda_addon_update

Do NOT use Addon Manager "Install from GitHub" on the monorepo root URL.
The repo name does not match subdir=cuda_addon_update.

Homepage: https://github.com/scottdd/cudatext_plugins/tree/main/addon_update
License: MPL 2.0
