# passenger_wsgi.py — WAJIB untuk konfigurasi Python App di cPanel/LiteSpeed
# cPanel secara otomatis mencari variabel "application" di file ini.
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from app import app as application  # noqa
