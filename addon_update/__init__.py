"""CudaText plugin: auto-update installed add-ons on a timer."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import traceback

__version__ = '0.1.0'

from cudatext import *
from cudax_lib import get_translation

from . import logic

_ = get_translation(__file__)

FN_CONFIG = os.path.join(app_path(APP_DIR_SETTINGS), 'cuda_addon_update.json')
TIMER_TICK = 'cuda_addon_update.on_timer'
TIMER_STARTUP = 'cuda_addon_update.on_startup_delay'

# Avoid overlapping runs
_busy = False


def _load_addonman_opt():
    """Ensure cuda_addonman.opt has user channels from its config file."""
    import cuda_addonman.opt as opt
    fn = os.path.join(app_path(APP_DIR_SETTINGS), 'cuda_addonman.json')
    if os.path.isfile(fn):
        try:
            data = json.loads(open(fn, encoding='utf-8').read())
            opt.ch_user = data.get('channels_user', opt.ch_user)
            opt.proxy = data.get('proxy', opt.proxy)
            opt.verify_https = data.get('verify_https', True)
            opt.sf_mirror = data.get('sf_mirror', '')
        except Exception:
            print('cuda_addon_update: cannot read cuda_addonman.json')
            traceback.print_exc()
    return opt


def _quiet_get_url(url: str, dest: str, timeout: int = 30, proxy: str = '', verify: bool = True) -> bool:
    """Download without Addon Manager Retry/Abort dialogs."""
    try:
        import requests
    except ImportError:
        print('cuda_addon_update: requests not available')
        return False
    proxies = {'http': proxy, 'https': proxy} if proxy else None
    if not verify:
        try:
            requests.packages.urllib3.disable_warnings()
        except Exception:
            pass
    tmp = dest + '.download'
    try:
        if os.path.isfile(tmp):
            os.remove(tmp)
        r = requests.get(url, proxies=proxies, verify=verify, stream=True, timeout=timeout)
        r.raise_for_status()
        with open(tmp, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        if os.path.getsize(tmp) == 0:
            os.remove(tmp)
            return False
        if os.path.isfile(dest):
            os.remove(dest)
        os.rename(tmp, dest)
        return True
    except Exception as e:
        print('cuda_addon_update: download failed:', url, e)
        if os.path.isfile(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        return False


def _fetch_channel_list(url: str, cache_dir: str, opt) -> list:
    import re
    from urllib.parse import unquote

    os.makedirs(cache_dir, exist_ok=True)
    cap = url.rstrip('/').split('/')[-1] or 'channel.json'
    temp_fn = os.path.join(cache_dir, cap)
    # refresh if missing or older than addonman cache_minutes
    aged = True
    if os.path.isfile(temp_fn):
        age_min = (time.time() - os.path.getmtime(temp_fn)) / 60.0
        aged = age_min > getattr(opt, 'cache_minutes', 10)
    if aged:
        if not _quiet_get_url(url, temp_fn, timeout=getattr(opt, 'download_timeout', 30),
                              proxy=getattr(opt, 'proxy', ''), verify=getattr(opt, 'verify_https', True)):
            return []
    try:
        text = open(temp_fn, encoding='utf-8').read()
        data = json.loads(text)
    except Exception as e:
        print('cuda_addon_update: bad channel', cap, e)
        return []
    if not isinstance(data, list):
        return []
    re_zip = re.compile(r'http.+/(\w+)\.(.+?)\.zip')
    for item in data:
        m = re_zip.findall(item.get('url', ''))
        if m:
            item['kind'] = m[0][0]
            item['name'] = unquote(m[0][1])
    return data


def _get_remote_addons(opt) -> list:
    channels = list(getattr(opt, 'ch_def', []) or []) + list(getattr(opt, 'ch_user', []) or [])
    cache_dir = os.path.join(tempfile.gettempdir(), 'cuda_addon_update_channels')
    out = []
    print('cuda_addon_update: reading channels…')
    for ch in channels:
        items = _fetch_channel_list(ch, cache_dir, opt)
        if items:
            out.extend(items)
    return out


class Command:
    def __init__(self):
        self.cfg = self._read_config()

    def _read_config(self):
        raw = None
        if os.path.isfile(FN_CONFIG):
            try:
                raw = json.loads(open(FN_CONFIG, encoding='utf-8').read())
            except Exception:
                print('cuda_addon_update: bad config, using defaults')
                traceback.print_exc()
        return logic.merge_config(raw)

    def _write_config(self):
        data = {k: self.cfg[k] for k in logic.DEFAULT_CONFIG}
        with open(FN_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            f.write('\n')

    def on_start(self, ed_self):
        self.cfg = self._read_config()
        if not self.cfg['enabled']:
            return
        # Short poll timer decides whether the long interval has elapsed
        poll_ms = max(60_000, int(self.cfg['poll_minutes']) * 60_000)
        timer_proc(TIMER_START, TIMER_TICK, poll_ms)
        if self.cfg['check_on_startup']:
            delay_ms = max(0, int(self.cfg['startup_delay_sec']) * 1000)
            if delay_ms <= 0:
                self._run_check(reason='startup')
            else:
                timer_proc(TIMER_START_ONE, TIMER_STARTUP, delay_ms)

    def on_startup_delay(self, tag='', info=''):
        self._run_check(reason='startup')

    def on_timer(self, tag='', info=''):
        self.cfg = self._read_config()
        if not self.cfg['enabled']:
            return
        if logic.interval_elapsed(self.cfg['last_check_unix'], self.cfg['interval_hours']):
            self._run_check(reason='interval')

    def check_now(self):
        self._run_check(reason='manual', force=True)

    def show_last_result(self):
        self.cfg = self._read_config()
        msg = self.cfg.get('last_result') or _('(no check yet)')
        msg_box(msg, MB_OK + MB_ICONINFO)

    def config(self):
        """Open JSON config in the editor (create with defaults if missing)."""
        self.cfg = self._read_config()
        self._write_config()
        file_open(FN_CONFIG)
        msg_status(_('Addon Update: edit JSON, save, then Plugins → Addon Update → Reload config'))

    def reload_config(self):
        self.cfg = self._read_config()
        timer_proc(TIMER_STOP, TIMER_TICK, 0)
        if self.cfg['enabled']:
            poll_ms = max(60_000, int(self.cfg['poll_minutes']) * 60_000)
            timer_proc(TIMER_START, TIMER_TICK, poll_ms)
        msg_status(_('Addon Update: config reloaded (interval=%sh)') % self.cfg['interval_hours'])

    def _run_check(self, reason='interval', force=False):
        global _busy
        if _busy:
            msg_status(_('Addon Update: already running'))
            return
        self.cfg = self._read_config()
        if not force and not self.cfg['enabled']:
            return
        if not force and not logic.interval_elapsed(self.cfg['last_check_unix'], self.cfg['interval_hours']):
            return

        _busy = True
        try:
            summary = self._do_updates()
        except Exception as e:
            summary = 'Error: %s' % e
            print('cuda_addon_update: exception')
            traceback.print_exc()
        finally:
            _busy = False

        self.cfg = self._read_config()
        self.cfg['last_check_unix'] = time.time()
        self.cfg['last_result'] = '[%s] %s' % (reason, summary)
        self._write_config()

        if self.cfg.get('notify'):
            msg_status(_('Addon Update: ') + summary)
        if self.cfg.get('notify_dialog') and (
            summary.startswith('updated:') or 'git pull:' in summary
        ):
            msg_box(_('Addon Update') + '\n\n' + summary, MB_OK + MB_ICONINFO)
        print('cuda_addon_update:', self.cfg['last_result'])

    def _do_updates(self) -> str:
        from cuda_addonman.work_local import (
            DIR_PY,
            do_remove_dir,
            do_save_version,
            get_addon_version,
            get_installed_addons,
            get_installed_modules,
            get_name_of_module,
        )

        opt = _load_addonman_opt()
        remote = _get_remote_addons(opt)
        if not remote:
            return 'Cannot download addon channel list'

        modules = get_installed_modules()
        modules_git = [m for m in modules if os.path.isdir(os.path.join(DIR_PY, m, '.git'))]
        modules_zip = [m for m in modules if m not in modules_git]

        installed = get_installed_addons()
        kinds = logic.allowed_kinds(self.cfg)

        # Never auto-replace this plugin mid-run (optional); still allow if outdated next time
        skip = set()

        outdated = logic.select_outdated(
            remote,
            modules_zip,
            installed,
            get_addon_version,
            kinds,
            skip_modules=skip,
        )

        updated = []
        failed = []
        git_updated = []
        git_failed = []

        # Git pulls for enabled plugin updates
        if 'plugin' in kinds:
            for m in modules_git:
                if m in logic.STD_MODULES:
                    continue
                m_dir = os.path.join(DIR_PY, m)
                msg_status(_('Addon Update: git pull %s') % m, True)
                try:
                    subprocess.call(['git', 'stash', 'save'], cwd=m_dir)
                    rc = subprocess.call(['git', 'pull'], cwd=m_dir)
                    if rc == 0:
                        git_updated.append(get_name_of_module(m))
                    else:
                        git_failed.append(get_name_of_module(m))
                except Exception as e:
                    print('cuda_addon_update: git error', m, e)
                    git_failed.append(get_name_of_module(m))

        total = len(outdated)
        for idx, a in enumerate(outdated):
            name = a.get('name') or a.get('module') or '?'
            url = a.get('url') or ''
            msg_status(
                _('Addon Update: ({}/{}) {}').format(idx + 1, total, name),
                True,
            )
            if not url:
                failed.append(name)
                continue
            fn = os.path.join(tempfile.gettempdir(), 'cuda_addon_update_addon.zip')
            ok = _quiet_get_url(
                url,
                fn,
                timeout=getattr(opt, 'download_timeout', 30),
                proxy=getattr(opt, 'proxy', ''),
                verify=getattr(opt, 'verify_https', True),
            )
            if not ok:
                failed.append(name)
                continue

            dir_to_remove = ''
            m = a.get('module', '')
            if m and a.get('kind') in ('plugin', 'treehelper', 'linter', 'formatter'):
                dir_to_remove = os.path.join(DIR_PY, m)

            if dir_to_remove and os.path.isdir(dir_to_remove):
                if not do_remove_dir(dir_to_remove):
                    failed.append(name)
                    continue

            if os.path.isfile(fn) and file_open(fn, options='/silent'):
                do_save_version(url, fn, a.get('v', ''))
                updated.append(name)
            else:
                failed.append(name)
                print('cuda_addon_update: silent install failed', name)

        return logic.format_result_summary(updated, failed, git_updated, git_failed)
