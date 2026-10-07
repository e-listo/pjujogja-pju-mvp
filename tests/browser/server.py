"""Server browser-test khusus CI; jangan jalankan pada database produksi."""
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from sqlalchemy.engine import make_url
uri=os.environ['PIJAR_TEST_DB_URI']
if os.getenv('PIJAR_DISPOSABLE_DB')!='yes' or make_url(uri).database!='pijar_bulk_test':
    raise RuntimeError('Database disposable pijar_bulk_test wajib')
os.environ['DATABASE_URL']=uri
os.environ['JWT_SECRET']='ci-browser-only-not-production-secret-123456789'
os.environ['SECRET_KEY']=os.environ['JWT_SECRET']
from flask import request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash
from passenger_wsgi import application
from models import db, Pengguna, KategoriPJU, Wilayah
from auth_routes import _BLACKLIST

@application.route('/__test__/reset',methods=['POST'])
def reset():
    if request.headers.get('X-Test-Reset')!='ci-only':return jsonify(success=False),403
    db.session.remove();db.drop_all();db.create_all();_BLACKLIST.clear()
    for role in ('admin','koordinator','teknisi'):
        db.session.add(Pengguna(nama_lengkap=role,username=role,password_hash=generate_password_hash('ci-only'),peran=role,status_aktif=True))
    db.session.add(KategoriPJU(id=1,kode='PJUP',nama='Uji',aktif=True))
    db.session.add(Wilayah(id_wilayah=1,kode_wilayah='UH2',nama_kelurahan='Uji',nama_kemantren='Uji'))
    db.session.commit();return jsonify(success=True)

@application.route('/test-ui/<path:filename>')
def frontend(filename):
    return send_from_directory(ROOT/'frontend'/'admin',filename)

if __name__=='__main__':
    application.run(host='127.0.0.1',port=5000,debug=False,use_reloader=False)
