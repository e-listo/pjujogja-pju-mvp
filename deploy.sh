#!/bin/bash
# ============================================================
# deploy.sh — PIJAR UPT PJU Kota Yogyakarta
# Jalankan dari direktori ~/admin.pjujogja.id
# Usage: ./deploy.sh
#
# Setelah deploy, restart Python App (api.pjujogja.id) manual:
#   touch ~/api.pjujogja.id/tmp/restart.txt
# ============================================================

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

echo "🔄 [1/4] Git pull..."
git pull origin main

echo "📋 [2/4] Copy halaman admin ke root..."
cp frontend/admin/*.html .
cp frontend/admin/js/sidebar.js js/
cp frontend/admin/js/auth.js js/ 2>/dev/null || true

echo "📱 [3/4] Copy halaman lapangan..."
cp frontend/lapangan/*.html lapangan/

echo "✅ [4/4] Deploy selesai: $(date '+%Y-%m-%d %H:%M:%S WIB')"
echo ""
echo "File yang di-deploy:"
echo "  Admin   : $(ls frontend/admin/*.html | wc -l) halaman"
echo "  Lapangan: $(ls frontend/lapangan/*.html | wc -l) halaman"
echo "  JS      : sidebar.js, auth.js"
echo ""
echo "💡 Jangan lupa restart API jika ada perubahan backend:"
echo "   touch ~/api.pjujogja.id/tmp/restart.txt"
