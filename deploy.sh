#!/bin/bash
# ============================================================
# deploy.sh — PIJAR UPT PJU Kota Yogyakarta
# Jalankan dari direktori ~/admin.pjujogja.id
# Usage: ./deploy.sh
# ============================================================

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

echo "🔄 [1/5] Git pull..."
git pull origin main

echo "📋 [2/5] Copy halaman admin ke root..."
cp frontend/admin/*.html .
cp frontend/admin/js/sidebar.js js/
cp frontend/admin/js/auth.js js/ 2>/dev/null || true

echo "📱 [3/5] Copy halaman lapangan..."
cp frontend/lapangan/*.html lapangan/

echo "🔁 [4/5] Restart Python App (api.pjujogja.id)..."
# Direktori API berada di ~/api.pjujogja.id, bukan di sini
mkdir -p ~/api.pjujogja.id/tmp
touch ~/api.pjujogja.id/tmp/restart.txt
echo "   ✓ restart.txt disentuh — Passenger akan reload otomatis"

echo "✅ [5/5] Deploy selesai: $(date '+%Y-%m-%d %H:%M:%S WIB')"
echo ""
echo "File yang di-deploy:"
echo "  Admin   : $(ls frontend/admin/*.html | wc -l) halaman"
echo "  Lapangan: $(ls frontend/lapangan/*.html | wc -l) halaman"
echo "  JS      : sidebar.js, auth.js"
echo ""
echo "💡 Tip: jika API belum reload, jalankan manual:"
echo "   touch ~/api.pjujogja.id/tmp/restart.txt"
