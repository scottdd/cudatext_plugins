#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
STAGE="$(mktemp -d)"
OUT="$ROOT/dist"
ZIP="$OUT/plugin.Addon_Update.zip"

cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT

mkdir -p "$STAGE" "$OUT"

rsync -a \
  --exclude __pycache__ \
  --exclude '*.pyc' \
  --exclude .git \
  --exclude .gitignore \
  --exclude dist \
  --exclude pack.sh \
  --exclude addon-channel.json \
  --exclude release.json \
  --exclude tests \
  "$ROOT/" "$STAGE/"

find "$STAGE" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

rm -f "$ZIP"
(
  cd "$STAGE"
  zip -r "$ZIP" .
)

echo "Created $ZIP"
unzip -l "$ZIP" | head -20 || true
