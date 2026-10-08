"""
Tes API manajemen pengguna (khusus admin) dan ubah password sendiri.
Nama berkas mengikuti pola test_aset_bulk*.py agar ikut dijalankan CI (MariaDB).
"""
import os
import unittest


@unittest.skipUnless(os.getenv('PIJAR_DISPOSABLE_DB') == 'yes', 'Database uji belum tersedia')
class PenggunaAPITests(unittest.TestCase):
    PW = 'ci-only-1234'

    def setUp(self):
        from flask import Flask
        from sqlalchemy.engine import make_url
        from werkzeug.security import generate_password_hash
        from models import db, Pengguna, Regu
        from auth_routes import auth_bp, _BLACKLIST
        uri = os.environ['PIJAR_TEST_DB_URI']
        if make_url(uri).database != 'pijar_bulk_test':
            raise RuntimeError('Database uji wajib pijar_bulk_test')
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            JWT_SECRET='ci-only-not-production-secret-123456789',
            JWT_EXP_HOURS=1,
            SQLALCHEMY_DATABASE_URI=uri,
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.app.register_blueprint(auth_bp)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.db = db
        _BLACKLIST.clear()
        self.addCleanup(self.cleanup)
        db.drop_all()
        db.create_all()
        for role in ('admin', 'koordinator', 'teknisi'):
            db.session.add(Pengguna(
                nama_lengkap=role.title(), username=role,
                password_hash=generate_password_hash(self.PW), peran=role, status_aktif=True,
            ))
        db.session.add(Regu(id_regu=1, nama_regu='Regu Uji 1', status_aktif=True))
        db.session.add(Regu(id_regu=2, nama_regu='Regu Nonaktif', status_aktif=False))
        db.session.commit()
        self.client = self.app.test_client()

    def cleanup(self):
        self.db.session.rollback()
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def login(self, username, password=None):
        return self.client.post('/api/auth/login', json={'username': username, 'password': password or self.PW})

    def header(self, username='admin'):
        r = self.login(username)
        self.assertEqual(r.status_code, 200)
        return {'Authorization': 'Bearer ' + r.get_json()['token']}

    def buat(self, username='budi', **extra):
        body = {'nama_lengkap': username.title(), 'username': username, 'password': 'rahasia-123', 'peran': 'teknisi'}
        body.update(extra)
        return self.client.post('/api/pengguna', json=body, headers=self.header())

    def test_tanpa_token_ditolak(self):
        self.assertEqual(self.client.get('/api/pengguna').status_code, 401)

    def test_hanya_admin(self):
        for role in ('koordinator', 'teknisi'):
            with self.subTest(role=role):
                h = self.header(role)
                self.assertEqual(self.client.get('/api/pengguna', headers=h).status_code, 403)
                self.assertEqual(self.client.post('/api/pengguna', json={}, headers=h).status_code, 403)
                self.assertEqual(self.client.patch('/api/pengguna/1', json={'peran': 'admin'}, headers=h).status_code, 403)
                self.assertEqual(self.client.post('/api/pengguna/1/reset-password', json={'password': 'abcdefgh1'}, headers=h).status_code, 403)

    def test_buat_teknisi_tanpa_regu_lalu_login(self):
        r = self.buat('budi')
        self.assertEqual(r.status_code, 201)
        data = r.get_json()['data']
        self.assertEqual(data['username'], 'budi')
        self.assertEqual(data['peran'], 'teknisi')
        self.assertIsNone(data['id_regu'])
        self.assertIsNone(data['nama_regu'])
        self.assertNotIn('password_hash', data)
        self.assertNotIn('password', data)
        self.assertEqual(self.login('budi', 'rahasia-123').status_code, 200)

    def test_username_duplikat(self):
        self.assertEqual(self.buat('budi').status_code, 201)
        self.assertEqual(self.buat('budi').status_code, 409)

    def test_validasi_input(self):
        from models import Pengguna
        self.assertEqual(self.buat('budi', password='pendek').status_code, 400)
        self.assertEqual(self.buat('b d').status_code, 400)
        self.assertEqual(self.buat('budi', peran='regu').status_code, 400)
        self.assertEqual(self.buat('budi', id_regu=999).status_code, 400)
        self.assertEqual(self.buat('budi', id_regu=2).status_code, 400)
        self.assertEqual(self.buat('budi', no_hp='abc').status_code, 400)
        self.assertEqual(self.buat('budi', nama_lengkap='   ').status_code, 400)
        self.assertEqual(Pengguna.query.filter_by(username='budi').count(), 0)

    def test_regu_boleh_kosong_dan_diganti(self):
        r = self.buat('sari', id_regu=1)
        self.assertEqual(r.status_code, 201)
        d = r.get_json()['data']
        self.assertEqual(d['id_regu'], 1)
        self.assertEqual(d['nama_regu'], 'Regu Uji 1')
        url = '/api/pengguna/%d' % d['id_pengguna']
        r = self.client.patch(url, json={'id_regu': None}, headers=self.header())
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.get_json()['data']['id_regu'])
        r = self.client.put(url, json={'id_regu': 1}, headers=self.header())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['data']['id_regu'], 1)

    def test_nonaktifkan_langsung_memutus_akses(self):
        pid = self.buat('doni').get_json()['data']['id_pengguna']
        token = self.login('doni', 'rahasia-123').get_json()['token']
        hd = {'Authorization': 'Bearer ' + token}
        self.assertEqual(self.client.get('/api/auth/me', headers=hd).status_code, 200)
        url = '/api/pengguna/%d' % pid
        r = self.client.patch(url, json={'status_aktif': False}, headers=self.header())
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.get_json()['data']['status_aktif'])
        self.assertEqual(self.client.get('/api/auth/me', headers=hd).status_code, 401)
        self.assertEqual(self.login('doni', 'rahasia-123').status_code, 401)
        r = self.client.patch(url, json={'status_aktif': True}, headers=self.header())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.login('doni', 'rahasia-123').status_code, 200)

    def test_admin_tidak_boleh_mengunci_diri(self):
        from models import Pengguna
        pid = Pengguna.query.filter_by(username='admin').one().id_pengguna
        url = '/api/pengguna/%d' % pid
        h = self.header()
        self.assertEqual(self.client.patch(url, json={'status_aktif': False}, headers=h).status_code, 409)
        self.assertEqual(self.client.patch(url, json={'peran': 'teknisi'}, headers=h).status_code, 409)
        self.assertEqual(self.client.get('/api/auth/me', headers=h).status_code, 200)
        r = self.client.patch(url, json={'nama_lengkap': 'Admin Baru'}, headers=h)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['data']['nama_lengkap'], 'Admin Baru')

    def test_ubah_peran_akun_lain_langsung_berlaku(self):
        pid = self.buat('eko').get_json()['data']['id_pengguna']
        hd = {'Authorization': 'Bearer ' + self.login('eko', 'rahasia-123').get_json()['token']}
        self.assertEqual(self.client.get('/api/pengguna', headers=hd).status_code, 403)
        r = self.client.patch('/api/pengguna/%d' % pid, json={'peran': 'admin'}, headers=self.header())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['data']['peran'], 'admin')
        self.assertEqual(self.client.get('/api/pengguna', headers=hd).status_code, 200)

    def test_username_diubah_tidak_boleh_bentrok(self):
        pid = self.buat('fani').get_json()['data']['id_pengguna']
        url = '/api/pengguna/%d' % pid
        self.assertEqual(self.client.patch(url, json={'username': 'admin'}, headers=self.header()).status_code, 409)
        self.assertEqual(self.client.patch(url, json={'username': 'fani2'}, headers=self.header()).status_code, 200)
        self.assertEqual(self.client.patch(url, json={}, headers=self.header()).status_code, 400)
        self.assertEqual(self.client.patch(url, json={'password': 'abcdefgh1'}, headers=self.header()).status_code, 400)

    def test_reset_password(self):
        pid = self.buat('rini').get_json()['data']['id_pengguna']
        url = '/api/pengguna/%d/reset-password' % pid
        self.assertEqual(self.client.post(url, json={'password': 'pendek'}, headers=self.header()).status_code, 400)
        self.assertEqual(self.client.post(url, json={'password': 'baru-12345'}, headers=self.header()).status_code, 200)
        self.assertEqual(self.login('rini', 'rahasia-123').status_code, 401)
        self.assertEqual(self.login('rini', 'baru-12345').status_code, 200)
        self.assertEqual(self.client.post('/api/pengguna/9999/reset-password', json={'password': 'baru-12345'}, headers=self.header()).status_code, 404)

    def test_ubah_password_sendiri(self):
        self.buat('tono')
        hd = {'Authorization': 'Bearer ' + self.login('tono', 'rahasia-123').get_json()['token']}
        url = '/api/auth/ubah-password'
        self.assertEqual(self.client.post(url, json={'password_lama': 'salah-salah', 'password_baru': 'baru-12345'}, headers=hd).status_code, 400)
        self.assertEqual(self.client.post(url, json={'password_lama': 'rahasia-123', 'password_baru': 'pendek'}, headers=hd).status_code, 400)
        self.assertEqual(self.client.post(url, json={'password_lama': 'rahasia-123', 'password_baru': 'rahasia-123'}, headers=hd).status_code, 400)
        self.assertEqual(self.client.post(url, json={'password_lama': 'rahasia-123', 'password_baru': 'baru-12345'}, headers=hd).status_code, 200)
        self.assertEqual(self.login('tono', 'rahasia-123').status_code, 401)
        self.assertEqual(self.login('tono', 'baru-12345').status_code, 200)

    def test_daftar_dan_filter(self):
        self.buat('anto', id_regu=1)
        pid = self.buat('bayu').get_json()['data']['id_pengguna']
        self.client.patch('/api/pengguna/%d' % pid, json={'status_aktif': False}, headers=self.header())
        h = self.header()

        def ambil(query=''):
            r = self.client.get('/api/pengguna' + query, headers=h)
            self.assertEqual(r.status_code, 200)
            return r.get_json()

        semua = ambil()
        self.assertEqual(semua['meta']['total'], 5)
        self.assertEqual([p['username'] for p in ambil('?q=anto')['data']], ['anto'])
        self.assertEqual([p['username'] for p in ambil('?status=nonaktif')['data']], ['bayu'])
        self.assertEqual(ambil('?status=aktif')['meta']['total'], 4)
        self.assertEqual(ambil('?peran=admin')['meta']['total'], 1)
        self.assertEqual([p['username'] for p in ambil('?id_regu=1')['data']], ['anto'])
        self.assertEqual(ambil('?id_regu=kosong')['meta']['total'], 4)
        hal2 = ambil('?per_page=2&page=2')
        self.assertEqual(len(hal2['data']), 2)
        self.assertEqual(hal2['meta']['total_pages'], 3)
        self.assertEqual(self.client.get('/api/pengguna?peran=xyz', headers=h).status_code, 400)
        self.assertEqual(self.client.get('/api/pengguna?status=xyz', headers=h).status_code, 400)

    def test_detail_dan_tidak_ada_hapus(self):
        h = self.header()
        self.assertEqual(self.client.get('/api/pengguna/9999', headers=h).status_code, 404)
        r = self.client.get('/api/pengguna/1', headers=h)
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('password_hash', r.get_json()['data'])
        self.assertEqual(self.client.delete('/api/pengguna/1', headers=h).status_code, 405)


if __name__ == '__main__':
    unittest.main()
