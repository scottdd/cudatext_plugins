#!/usr/bin/env python3
"""Build a plugin zip, update addons/plugins.json, push, and publish a GitHub release."""

from __future__ import annotations

import argparse
import configparser
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHANNEL = ROOT / "addons" / "plugins.json"


class ReleaseError(Exception):
    pass


def run(cmd: list[str], *, cwd: Path | None = None, dry_run: bool = False) -> None:
    line = " ".join(cmd)
    print(f"+ {line}")
    if dry_run:
        return
    subprocess.run(cmd, cwd=cwd, check=True)


def read_install_inf(plugin_dir: Path) -> dict[str, str]:
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(plugin_dir / "install.inf", encoding="utf-8")
    if "info" not in parser:
        raise ReleaseError(f"Missing [info] in {plugin_dir / 'install.inf'}")
    return dict(parser["info"])


def read_release_meta(plugin_dir: Path) -> dict:
    path = plugin_dir / "release.json"
    if not path.is_file():
        raise ReleaseError(f"Missing {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_github_slug(remote_url: str) -> str:
    match = re.search(r"github\.com[:/](?P<slug>[^/]+/[^/]+?)(?:\.git)?$", remote_url.strip())
    if not match:
        raise ReleaseError(f"Cannot parse GitHub slug from remote URL: {remote_url}")
    return match.group("slug")


def read_repo_slug() -> str:
    out = subprocess.check_output(
        ["git", "remote", "get-url", "origin"],
        cwd=ROOT,
        text=True,
    ).strip()
    return parse_github_slug(out)


def read_version_from_init(plugin_dir: Path) -> str | None:
    init_py = plugin_dir / "__init__.py"
    if not init_py.is_file():
        return None
    match = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", init_py.read_text(encoding="utf-8"), re.M)
    return match.group(1) if match else None


def notes_from_history(history_path: Path, *, max_lines: int = 8) -> str:
    if not history_path.is_file():
        return ""
    lines = history_path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[:max_lines]).strip()


def load_channel() -> list[dict]:
    if not CHANNEL.is_file():
        return []
    data = json.loads(CHANNEL.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ReleaseError(f"{CHANNEL} must contain a JSON array")
    return data


def save_channel(entries: list[dict], *, dry_run: bool) -> None:
    text = json.dumps(entries, indent=2) + "\n"
    print(f"Updating {CHANNEL}")
    if dry_run:
        print(text)
        return
    CHANNEL.write_text(text, encoding="utf-8")


def upsert_channel_entry(
    entries: list[dict],
    *,
    module: str,
    desc: str,
    version: str,
    url: str,
) -> list[dict]:
    entry = {"url": url, "desc": desc, "module": module, "v": version}
    for idx, item in enumerate(entries):
        if item.get("module") == module:
            entries[idx] = entry
            return entries
    entries.append(entry)
    entries.sort(key=lambda item: item.get("module", ""))
    return entries


def sync_addon_channel(plugin_dir: Path, entry: dict, *, dry_run: bool) -> None:
    path = plugin_dir / "addon-channel.json"
    text = json.dumps([entry], indent=2) + "\n"
    print(f"Updating {path}")
    if dry_run:
        print(text)
        return
    path.write_text(text, encoding="utf-8")


def git_has_staged_changes(paths: list[str], *, cwd: Path) -> bool:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *paths],
        cwd=cwd,
    )
    if proc.returncode == 0:
        return False
    if proc.returncode == 1:
        return True
    raise ReleaseError("git diff --cached failed")


def commit_release_files(paths: list[Path], message: str, *, dry_run: bool) -> bool:
    rel = [str(p) for p in paths]
    if dry_run:
        print(f"+ git add -- {' '.join(rel)}")
        print(f"+ git commit -m {message!r} -- {' '.join(rel)}")
        return True
    run(["git", "add", "--", *rel], cwd=ROOT, dry_run=False)
    if not git_has_staged_changes(rel, cwd=ROOT):
        print("No release changes to commit")
        return False
    run(["git", "commit", "-m", message, "--", *rel], cwd=ROOT, dry_run=False)
    return True


def release_exists(tag: str, repo: str, *, dry_run: bool) -> bool:
    if dry_run:
        return False
    proc = subprocess.run(
        ["gh", "release", "view", tag, "--repo", repo],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def publish_github_release(
    *,
    tag: str,
    repo: str,
    zip_path: Path,
    title: str,
    notes: str,
    dry_run: bool,
) -> None:
    if release_exists(tag, repo, dry_run=dry_run):
        run(
            [
                "gh",
                "release",
                "edit",
                tag,
                "--repo",
                repo,
                "--title",
                title,
                "--notes",
                notes,
            ],
            cwd=ROOT,
            dry_run=dry_run,
        )
        run(
            ["gh", "release", "upload", tag, str(zip_path), "--repo", repo, "--clobber"],
            cwd=ROOT,
            dry_run=dry_run,
        )
        return
    run(
        [
            "gh",
            "release",
            "create",
            tag,
            str(zip_path),
            "--repo",
            repo,
            "--title",
            title,
            "--notes",
            notes,
        ],
        cwd=ROOT,
        dry_run=dry_run,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin", help="Plugin directory name, e.g. cuda-tabmenu")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without changing anything")
    parser.add_argument("--no-git", action="store_true", help="Skip git commit and push")
    parser.add_argument("--no-github", action="store_true", help="Skip GitHub release upload")
    parser.add_argument(
        "--notes",
        help="Release notes text or path to a file (default: plugin readme/history.txt excerpt)",
    )
    args = parser.parse_args()

    plugin_dir = ROOT / args.plugin
    if not plugin_dir.is_dir():
        raise ReleaseError(f"Plugin directory not found: {plugin_dir}")

    info = read_install_inf(plugin_dir)
    release_meta = read_release_meta(plugin_dir)

    version = info.get("version", "").strip()
    module = info.get("subdir", "").strip()
    title = info.get("title", args.plugin).strip()
    desc = info.get("desc", "").strip()
    zip_name = release_meta.get("zip", "").strip()

    if not version:
        raise ReleaseError("install.inf is missing version=")
    if not module:
        raise ReleaseError("install.inf is missing subdir=")
    if not zip_name:
        raise ReleaseError("release.json is missing zip")

    init_version = read_version_from_init(plugin_dir)
    if init_version and init_version != version:
        raise ReleaseError(
            f"Version mismatch: install.inf has {version}, __init__.py has {init_version}"
        )

    pack_sh = plugin_dir / "pack.sh"
    if not pack_sh.is_file():
        raise ReleaseError(f"Missing {pack_sh}")

    repo = read_repo_slug()
    tag = f"{args.plugin}-v{version}"
    zip_path = plugin_dir / "dist" / zip_name
    download_url = f"https://github.com/{repo}/releases/download/{tag}/{zip_name}"

    print(f"Plugin: {title} ({module})")
    print(f"Version: {version}")
    print(f"Tag: {tag}")
    print(f"Zip: {zip_path}")
    print(f"Channel URL: {download_url}")

    run(["bash", str(pack_sh)], cwd=plugin_dir, dry_run=args.dry_run)
    if not args.dry_run and not zip_path.is_file():
        raise ReleaseError(f"Pack script did not create {zip_path}")

    channel_entry = {
        "url": download_url,
        "desc": desc,
        "module": module,
        "v": version,
    }
    channel = upsert_channel_entry(
        load_channel(),
        module=module,
        desc=desc,
        version=version,
        url=download_url,
    )
    save_channel(channel, dry_run=args.dry_run)
    sync_addon_channel(plugin_dir, channel_entry, dry_run=args.dry_run)

    commit_names = [
        CHANNEL.relative_to(ROOT),
        (plugin_dir / "addon-channel.json").relative_to(ROOT),
        (plugin_dir / "install.inf").relative_to(ROOT),
        (plugin_dir / "__init__.py").relative_to(ROOT),
        (plugin_dir / "readme" / "history.txt").relative_to(ROOT),
    ]
    if not args.no_git:
        committed = commit_release_files(
            commit_names,
            f"Release {args.plugin} v{version}",
            dry_run=args.dry_run,
        )
        if committed or not args.dry_run:
            run(["git", "push", "origin", "main"], cwd=ROOT, dry_run=args.dry_run)

    if not args.no_github:
        if args.notes:
            notes_path = Path(args.notes)
            notes = notes_path.read_text(encoding="utf-8") if notes_path.is_file() else args.notes
        else:
            notes = notes_from_history(plugin_dir / "readme" / "history.txt")
        notes = notes or f"{title} {version}"
        publish_github_release(
            tag=tag,
            repo=repo,
            zip_path=zip_path,
            title=f"{title} {version}",
            notes=notes,
            dry_run=args.dry_run,
        )

    print("Done.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReleaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except subprocess.CalledProcessError as exc:
        print(f"error: command failed ({exc.returncode}): {' '.join(exc.cmd)}", file=sys.stderr)
        raise SystemExit(1)
