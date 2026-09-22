"""Pure helpers for Addons Update (testable without CudaText GUI)."""

from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

__version__ = '0.1.1'

PREINST = 'preinstalled'

# Stock modules Addon Manager treats as preinstalled (do not auto-replace).
STD_MODULES = frozenset({
    'cuda_addonman',
    'cuda_comments',
    'cuda_insert_time',
    'cuda_make_plugin',
    'cuda_multi_installer',
    'cuda_new_file',
    'cuda_prefs',
    'cuda_palette',
    'cuda_project_man',
    'cuda_snippet_panel',
    'cuda_sort',
    'cuda_tabs_list',
    'cuda_lexer_detecter',
})

DEFAULT_CONFIG: Dict[str, Any] = {
    'enabled': True,
    'interval_hours': 12,
    'check_on_startup': True,
    'startup_delay_sec': 45,
    'poll_minutes': 5,
    'notify': True,
    'notify_dialog': False,
    'update_plugins': True,
    'update_linters': True,
    'update_formatters': True,
    'update_treehelpers': True,
    'update_lexers': False,
    'update_themes': False,
    'update_translations': False,
    'last_check_unix': 0,
    'last_result': '',
}

# Sibling keys written into JSON as <param>_Hint (ignored when loading values).
CONFIG_HINTS: Dict[str, str] = {
    'enabled': 'Master switch for automatic checks',
    'interval_hours': 'Hours between automatic update checks',
    'check_on_startup': 'Run a check shortly after CudaText starts',
    'startup_delay_sec': 'Seconds to wait after start before first check',
    'poll_minutes': 'How often the idle timer wakes to see if interval elapsed',
    'notify': 'Show a status-bar line after each check',
    'notify_dialog': 'Pop a dialog when something was actually updated',
    'update_plugins': 'Update installed plugins from channels',
    'update_linters': 'Update installed linters',
    'update_formatters': 'Update installed formatters',
    'update_treehelpers': 'Update installed tree-helpers',
    'update_lexers': 'Update installed lexers (off by default)',
    'update_themes': 'Update installed themes (off by default)',
    'update_translations': 'Update UI translations (off by default)',
    'last_check_unix': 'Unix time of last completed check (auto-maintained)',
    'last_result': 'Summary text from last check (auto-maintained)',
}


def merge_config(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    if isinstance(raw, dict):
        for key, value in raw.items():
            if key.endswith('_Hint'):
                continue
            if key in cfg:
                cfg[key] = value
    # coerce / clamp
    try:
        cfg['interval_hours'] = max(0.25, float(cfg['interval_hours']))
    except (TypeError, ValueError):
        cfg['interval_hours'] = DEFAULT_CONFIG['interval_hours']
    try:
        cfg['startup_delay_sec'] = max(0, int(cfg['startup_delay_sec']))
    except (TypeError, ValueError):
        cfg['startup_delay_sec'] = DEFAULT_CONFIG['startup_delay_sec']
    try:
        cfg['poll_minutes'] = max(1, int(cfg['poll_minutes']))
    except (TypeError, ValueError):
        cfg['poll_minutes'] = DEFAULT_CONFIG['poll_minutes']
    for bkey in (
        'enabled', 'check_on_startup', 'notify', 'notify_dialog',
        'update_plugins', 'update_linters', 'update_formatters',
        'update_treehelpers', 'update_lexers', 'update_themes',
        'update_translations',
    ):
        cfg[bkey] = bool(cfg[bkey])
    try:
        cfg['last_check_unix'] = float(cfg.get('last_check_unix') or 0)
    except (TypeError, ValueError):
        cfg['last_check_unix'] = 0
    cfg['last_result'] = str(cfg.get('last_result') or '')
    return cfg


def interval_elapsed(last_unix: float, interval_hours: float, now: Optional[float] = None) -> bool:
    now = time.time() if now is None else now
    if last_unix <= 0:
        return True
    return (now - last_unix) >= (interval_hours * 3600.0)


def fix_name(s: str, del_brackets: bool) -> str:
    s = s.replace(' ', '_')
    if del_brackets:
        n = s.find('_(')
        if n >= 0:
            s = s[:n]
    return s


def allowed_kinds(cfg: Dict[str, Any]) -> Set[str]:
    kinds: Set[str] = set()
    if cfg.get('update_plugins'):
        kinds.add('plugin')
    if cfg.get('update_linters'):
        kinds.add('linter')
    if cfg.get('update_formatters'):
        kinds.add('formatter')
    if cfg.get('update_treehelpers'):
        kinds.add('treehelper')
    if cfg.get('update_lexers'):
        kinds.add('lexer')
    if cfg.get('update_themes'):
        kinds.add('theme')
    if cfg.get('update_translations'):
        kinds.add('translation')
    return kinds


def needs_update(v_local: str, v_remote: str) -> bool:
    if not v_remote:
        return False
    if v_local == PREINST:
        return False
    if not v_local or v_local == '?':
        return True
    # Addon Manager uses plain string compare for versions
    return v_local < v_remote


def select_outdated(
    remote_addons: Sequence[Dict[str, Any]],
    installed_modules: Sequence[str],
    installed_addons: Sequence[Dict[str, Any]],
    get_local_version,
    kinds: Set[str],
    skip_modules: Optional[Iterable[str]] = None,
) -> List[Dict[str, Any]]:
    """Return remote addon dicts that should be updated (zip path).

    get_local_version(url) -> local version string from packages.ini (may be '').
    """
    skip = set(skip_modules or ())
    modules = [m for m in installed_modules if m not in skip and m not in STD_MODULES]

    lexers = [fix_name(i['name'], False) for i in installed_addons if i.get('kind') == 'lexer']
    langs = [fix_name(i['name'], False) for i in installed_addons if i.get('kind') == 'translation']
    themes = [fix_name(i['name'], True).lower() for i in installed_addons if i.get('kind') == 'theme']

    selected: List[Dict[str, Any]] = []
    for a in remote_addons:
        kind = a.get('kind')
        if kind not in kinds:
            continue
        name = a.get('name', '')
        module = a.get('module', '') or ''

        if kind in ('plugin', 'treehelper', 'linter', 'formatter'):
            if module not in modules:
                continue
            if module in skip:
                continue
        elif kind == 'lexer':
            if name not in lexers:
                continue
        elif kind == 'translation':
            if name not in langs:
                continue
        elif kind == 'theme':
            if fix_name(name, True).lower() not in themes:
                continue
        else:
            continue

        url = a.get('url') or ''
        v_remote = a.get('v') or ''
        v_local = get_local_version(url) or ('?' if module not in STD_MODULES else PREINST)
        if module in STD_MODULES:
            v_local = PREINST
        if needs_update(v_local, v_remote):
            item = dict(a)
            item['v_local'] = v_local
            selected.append(item)
    return selected


def format_result_summary(
    updated: Sequence[str],
    failed: Sequence[str],
    git_updated: Sequence[str],
    git_failed: Sequence[str],
    skipped_reason: str = '',
) -> str:
    if skipped_reason:
        return skipped_reason
    parts: List[str] = []
    if updated:
        parts.append('updated: ' + ', '.join(updated))
    if git_updated:
        parts.append('git pull: ' + ', '.join(git_updated))
    if failed:
        parts.append('failed: ' + ', '.join(failed))
    if git_failed:
        parts.append('git failed: ' + ', '.join(git_failed))
    if not parts:
        return 'No addon updates needed'
    return '; '.join(parts)


def config_with_hints(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Ordered config dict with <key>_Hint after each value for JSON comments."""
    out: Dict[str, Any] = {}
    for key in DEFAULT_CONFIG:
        out[key] = cfg.get(key, DEFAULT_CONFIG[key])
        hint = CONFIG_HINTS.get(key)
        if hint:
            out[f'{key}_Hint'] = hint
    return out
