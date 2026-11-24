Plugin for CudaText: Addons Update (cuda_addon_update)
Version 0.1.1
Author: Scott (https://github.com/scottdd)

WHAT IS ADDONS UPDATE
  Addons Update looks at the add-ons you already have and installs newer
  versions from the channels configured in Addon Manager. That includes
  user channels, so plugins from this collection are covered along with
  official ones. You get a status-bar note when a check finishes, and you
  can turn on a dialog for checks that actually updated something.

  It runs a short time after CudaText starts, then again every 12 hours
  unless you change that. Zip-installed add-ons are downloaded and
  installed quietly, the same way Addon Manager installs them. A plugin
  you cloned with git is updated with "git stash save" and "git pull" in its
  folder. Stock modules that Addon Manager treats as preinstalled are
  skipped.

  Menus:
    Plugins → Addons Update → Check now
    Plugins → Addons Update → Show last result
    Plugins → Addons Update → Reload config
    Options → Settings-plugins → Addons Update → Config...

  Settings live in settings/cuda_addon_update.json. The keys you are most
  likely to change are interval_hours (hours between checks, default 12)
  and poll_minutes (how often the idle timer wakes to see whether that
  interval has elapsed, default 5).

HOW TO INSTALL

  TRUST
    Only add channels you trust. Adding a user channel lets CudaText
    download and run Python code from this repository with your user
    permissions. Future updates also come from this channel. The code is
    provided as-is, with no warranty (MPL-2.0). Please review the source
    and releases before installing:
      https://github.com/scottdd/cudatext_plugins
      https://github.com/scottdd/cudatext_plugins/releases

  QUICK INSTALL
    1. Options → Settings-plugins → Addons Manager → Config...
    2. In User channels, add this line:

         https://raw.githubusercontent.com/scottdd/cudatext_plugins/main/addons/scottdd-plugins.json

    3. Click OK, then Plugins → Addons Manager → Install... and choose
       Addons Update.

    The channel lists published release zips. A change on main is not
    installed until this plugin is released and the channel file is
    updated.

    On GitHub Releases, the Latest badge is whichever plugin was published
    most recently. Use the channel above, or open the Addons Update
    release.

    This plugin installs from that channel. The channels it later updates
    from are whatever you have configured in Addon Manager, including
    this one.

  MANUAL INSTALL
    1. Download plugin.Addons_Update.zip from GitHub Releases.
    2. In CudaText choose File → Open, open the zip, and confirm.
       The zip is flat (install.inf at the archive root). CudaText places
       that root in py/cuda_addon_update/. If you unzip by hand, extract
       into py/cuda_addon_update/ so install.inf sits directly in that
       folder. Do not leave the files loose in py/, and do not add an
       extra nested folder.
    3. Restart CudaText, or use Plugins → Reload plugins.

    py folder (install folder cuda_addon_update):

      Windows   <folder containing cudatext.exe>\py\
                Windows builds are portable. This is NOT %APPDATA%.
      macOS     ~/Library/Application Support/CudaText/py/
      Linux     ~/.config/cudatext/py/
                or $XDG_CONFIG_HOME/cudatext/py/
      Portable  <CudaText exe folder>/py/
                (.xz archives, or any exe next to a data/ folder)

    macOS and Linux need a system Python 3. Windows builds include Python.

SETTINGS
  Open Options → Settings-plugins → Addons Update → Config..., edit the
  JSON, save, then run Plugins → Addons Update → Reload config. The file
  is settings/cuda_addon_update.json. The first time you open Config, the
  file is created with these defaults.

    enabled              true     Master switch
    interval_hours       12       Hours between checks
    check_on_startup     true     Check after startup
    startup_delay_sec    45       Delay before the first check
    poll_minutes         5        How often the idle timer wakes to see
                                  whether the check interval has elapsed
    notify               true     Status-bar summary
    notify_dialog        false    Dialog when something updated
    update_plugins       true
    update_linters       true
    update_formatters    true
    update_treehelpers   true
    update_lexers        false
    update_themes        false
    update_translations  false

  poll_minutes is the wake-up period, not the update interval. A check
  runs when interval_hours has passed since the last one.

TROUBLESHOOTING
  Addons Update needs the built-in Addons Manager for channel lists and
  for the record of what is installed. A failed download is written to
  the Console. Automatic checks do not show Retry or Abort dialogs.
  Show last result opens the summary from the last check.

Homepage: https://github.com/scottdd/cudatext_plugins/tree/main/addon_update
License: MPL 2.0
Changelog: readme/history.txt and GitHub Releases
