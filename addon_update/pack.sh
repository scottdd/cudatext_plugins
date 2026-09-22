#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
STAGE="$(mktemp -d)"
OUT="$ROOT/dist"
# Addon Manager channel URLs must match: .../kind.Name.zip (see addon-channel.json)
ZIP="$OUT/plugin.Addons_Update.zip"

cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT

mkdir -p "$STAGE" "$OUT"

# Official CudaText plugin zips are FLAT: install.inf and __init__.py at the zip
# root. Addon Manager copies that unzip root into py/<subdir>/. Wrapping files
# in a cuda_addon_update/ folder installs as py/cuda_addon_update/cuda_addon_update/
# so Python imports an empty package and Command() never runs.
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
# head closes the pipe early; with pipefail that yields exit 141 (SIGPIPE)
unzip -l "$ZIP" | head -20 || true
