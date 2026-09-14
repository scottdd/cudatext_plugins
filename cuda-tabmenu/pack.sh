#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
STAGE="$(mktemp -d)"
OUT="$ROOT/dist"
# Addon Manager channel URLs must match: .../kind.Name.zip (see addon-channel.json)
ZIP="$OUT/plugin.Tab_Menu.zip"
SUBDIR=cuda_tabmenu

cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT

mkdir -p "$STAGE/$SUBDIR" "$OUT"

cp "$ROOT/install.inf" "$STAGE/"
rsync -a \
  --exclude __pycache__ \
  --exclude '*.pyc' \
  --exclude .git \
  --exclude .gitignore \
  --exclude dist \
  --exclude pack.sh \
  --exclude install.inf \
  --exclude addon-channel.json \
  --exclude release.json \
  --exclude tests \
  "$ROOT/" "$STAGE/$SUBDIR/"
cp "$ROOT/install.inf" "$STAGE/$SUBDIR/"

rm -rf "$STAGE/$SUBDIR/dist" 2>/dev/null || true
find "$STAGE" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

rm -f "$ZIP"
(
  cd "$STAGE"
  zip -r "$ZIP" install.inf "$SUBDIR"
)

echo "Created $ZIP"
# head closes the pipe early; with pipefail that yields exit 141 (SIGPIPE)
unzip -l "$ZIP" | head -20 || true
