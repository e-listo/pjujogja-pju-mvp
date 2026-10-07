#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
API_DIR="${PIJAR_API_DIR:-$HOME/api.pjujogja.id}"
PYTHON="${PIJAR_PYTHON:-$HOME/virtualenv/api.pjujogja.id/3.11/bin/python}"
MODE="${1:---dry-run}"
case "$MODE" in --dry-run|--apply) ;; *) echo "Usage: bash deploy-production.sh [--dry-run|--apply]"; exit 2;; esac
cd "$REPO_DIR"
echo "Repository: $REPO_DIR"
echo "API root: $API_DIR"
echo "Python: $PYTHON"
if [ "$MODE" = --dry-run ]; then
    echo "Plan: update main, install requirements, sync HTML/JS and backend allowlist; restart API."
    echo "No files or services changed. Backup and separate deployment approval required."
    exit 0
fi
[ -d "$API_DIR" ] && [ -x "$PYTHON" ] || { echo "API directory or Python missing"; exit 1; }
[ "$(git branch --show-current)" = main ] || { echo "Deploy main only"; exit 1; }
git diff --quiet && git diff --cached --quiet || { echo "Tracked working tree changes found"; exit 1; }
git pull --ff-only origin main
backend=(app.py auth_routes.py config.py models.py passenger_wsgi.py aset_bulk_service.py aset_bulk_routes.py requirements.txt)
for f in "${backend[@]}"; do
    [ -f "$f" ] && [ ! -L "$f" ] || { echo "Missing or symlink source: $f"; exit 1; }
    [ ! -L "$API_DIR/$f" ] || { echo "Refusing symlink target: $f"; exit 1; }
done
[ -f frontend/admin/js/aset-bulk.js ] && [ -f frontend/admin/js/detail-deeplink.js ]
"$PYTHON" -m pip install -r requirements.txt
mkdir -p js lapangan "$API_DIR/tmp"
cp frontend/admin/*.html .
cp frontend/admin/js/*.js js/
cp frontend/lapangan/*.html lapangan/
VERSION="$(git rev-parse --short HEAD)"
"$PYTHON" - "$REPO_DIR" "$VERSION" <<'PY'
import re, sys
from pathlib import Path
root, version = Path(sys.argv[1]), sys.argv[2]
for source in (root/'frontend/admin').glob('*.html'):
    target = root/source.name
    content = target.read_text(encoding='utf-8')
    content = re.sub(r'(js/detail-deeplink\.js)(?:\?[^"\s<>]*)?', lambda m: m.group(1)+'?v='+version, content)
    target.write_text(content, encoding='utf-8')
PY
for f in "${backend[@]}"; do cp "$f" "$API_DIR/$f"; done
"$PYTHON" -m py_compile "$API_DIR/models.py" "$API_DIR/aset_bulk_service.py" "$API_DIR/aset_bulk_routes.py" "$API_DIR/passenger_wsgi.py"
"$PYTHON" -c 'import openpyxl, jwt'
printf '%s\n' "$VERSION" > "$API_DIR/deployed_version.txt"
touch "$API_DIR/tmp/restart.txt"
echo "Deployment files updated at $VERSION. Verify API health, login and admin UI manually."
echo "No database migration, deletion, or overwrite of .env/upload directories performed."
