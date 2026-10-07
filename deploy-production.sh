#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob
fail() { echo "ERROR: $*" >&2; return 1; }
check_copy_dir() {
  local src="$1" dst="$2" f
  [ -d "$src" ] || { fail "Missing source directory: $src"; return 1; }
  if [ -L "$dst" ]; then
    [ -d "$dst" ] && [ "$src" -ef "$dst" ] || { fail "Unexpected directory symlink: $dst"; return 1; }
    return 0
  elif [ -e "$dst" ]; then
    [ -d "$dst" ] && [ -w "$dst" ] || { fail "Invalid destination directory: $dst"; return 1; }
  else
    [ -w "$(dirname "$dst")" ] || { fail "Destination parent not writable: $dst"; return 1; }
  fi
  [ ! "$src" -ef "$dst" ] || return 0
  for f in "$src"/*; do
    [ -f "$f" ] && [ ! -L "$f" ] || { fail "Unexpected source entry: $f"; return 1; }
    if [ -L "$dst/$(basename "$f")" ]; then
      fail "Refusing destination file symlink: $f"; return 1
    fi
  done
}
copy_directory_files() {
  local src="$1" dst="$2" files=("$1"/*)
  check_copy_dir "$src" "$dst"
  if [ "$src" -ef "$dst" ]; then
    echo "SKIP same directory: $dst"; return 0
  fi
  mkdir -p "$dst"
  if [ "${#files[@]}" -gt 0 ]; then cp "${files[@]}" "$dst/"; fi
}
check_page_target() {
  local src="$1" dst
  dst="$(basename "$src")"
  [ -f "$src" ] && [ ! -L "$src" ] || { fail "Invalid HTML source: $src"; return 1; }
  if [ -L "$dst" ]; then
    [ "$src" -ef "$dst" ] || { fail "Unexpected HTML symlink: $dst"; return 1; }
  elif [ -e "$dst" ]; then
    [ -f "$dst" ] && [ -w "$dst" ] || { fail "Invalid HTML target: $dst"; return 1; }
  fi
}
copy_pages() {
  local src dst
  for src in "$@"; do check_page_target "$src"; done
  for src in "$@"; do
    dst="$(basename "$src")"
    if [ -L "$dst" ]; then echo "SKIP same file: $dst"; else cp "$src" "$dst"; fi
  done
}
stamp_html_versions() {
  local python="$1" root="$2" version="$3"
  "$python" - "$root" "$version" <<'PY'
import re, sys
from pathlib import Path
root, version = Path(sys.argv[1]), sys.argv[2]
for source in (root/'frontend/admin').glob('*.html'):
    target = root/source.name
    if target.is_symlink() or not target.is_file():
        continue
    content = target.read_text(encoding='utf-8')
    content = re.sub(r'(js/detail-deeplink\.js)(?:\?[^"\s<>]*)?', lambda m: m.group(1)+'?v='+version, content)
    target.write_text(content, encoding='utf-8')
PY
}
main() {
  local mode="${1:---dry-run}" repo api python f version expected
  case "$mode" in --dry-run|--apply) ;; *) fail "Usage: bash deploy-production.sh [--dry-run|--apply]"; return 2;; esac
  repo="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  api="${PIJAR_API_DIR:-$HOME/api.pjujogja.id}"
  python="${PIJAR_PYTHON:-$HOME/virtualenv/api.pjujogja.id/3.11/bin/python}"
  cd "$repo"
  [ -d "$api" ] && [ -w "$api" ] && [ -x "$python" ] || { fail "API directory or Python invalid"; return 1; }
  [ ! "$repo" -ef "$api" ] || { fail "API root cannot equal repository"; return 1; }
  local backend=(app.py auth_routes.py config.py models.py passenger_wsgi.py aset_bulk_service.py aset_bulk_routes.py requirements.txt)
  local pages=(frontend/admin/*.html)
  [ "${#pages[@]}" -gt 0 ] && [ -f frontend/admin/js/aset-bulk.js ] && [ -f frontend/admin/js/detail-deeplink.js ] || { fail "Frontend sources incomplete"; return 1; }
  for f in "${backend[@]}"; do
    [ -f "$f" ] && [ ! -L "$f" ] && [ ! -L "$api/$f" ] || { fail "Invalid backend path: $f"; return 1; }
    if [ -e "$api/$f" ]; then [ -f "$api/$f" ] && [ -w "$api/$f" ] || { fail "Backend target not writable: $f"; return 1; }; fi
  done
  for f in "${pages[@]}"; do check_page_target "$f"; done
  [ -w "$repo" ] || { fail "Repository not writable"; return 1; }
  check_copy_dir frontend/admin/js js
  check_copy_dir frontend/lapangan lapangan
  [ ! -L "$api/tmp" ] && [ ! -L "$api/tmp/restart.txt" ] && [ ! -L "$api/deployed_version.txt" ] || { fail "Invalid API restart/version path"; return 1; }
  if [ -e "$api/tmp" ]; then [ -d "$api/tmp" ] && [ -w "$api/tmp" ] || { fail "Invalid tmp directory"; return 1; }; fi
  if [ -e "$api/tmp/restart.txt" ]; then [ -f "$api/tmp/restart.txt" ] && [ -w "$api/tmp/restart.txt" ] || { fail "Restart file not writable"; return 1; }; fi
  if [ -e "$api/deployed_version.txt" ]; then [ -f "$api/deployed_version.txt" ] && [ -w "$api/deployed_version.txt" ] || { fail "Version file not writable"; return 1; }; fi
  "$python" -c 'import sys; [compile(open(f, encoding="utf-8").read(), f, "exec") for f in sys.argv[1:]]' "${backend[@]:0:7}"
  if [ "$mode" = --dry-run ]; then echo "Preflight passed; no install, copy, pull, or restart performed."; return 0; fi
  [ "$(git branch --show-current)" = main ] || { fail "Deploy main only"; return 1; }
  expected="${PIJAR_EXPECTED_COMMIT:?Set approved full commit SHA}"
  [ "$(git rev-parse HEAD)" = "$expected" ] || { fail "HEAD differs from approved commit"; return 1; }
  git -c core.fileMode=false diff --quiet && git -c core.fileMode=false diff --cached --quiet || { fail "Tracked content changes found"; return 1; }
  "$python" -m pip install -r requirements.txt
  copy_pages "${pages[@]}"
  copy_directory_files frontend/admin/js js
  copy_directory_files frontend/lapangan lapangan
  version="$(git rev-parse --short HEAD)"
  stamp_html_versions "$python" "$repo" "$version"
  for f in "${backend[@]}"; do cp "$f" "$api/$f"; done
  "$python" -c 'import openpyxl, jwt'
  mkdir -p "$api/tmp"
  printf '%s\n' "$expected" > "$api/deployed_version.txt"
  touch "$api/tmp/restart.txt"
  echo "Files deployed at $expected. Verify health, login, UI and import manually."
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
