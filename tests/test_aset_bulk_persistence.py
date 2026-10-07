"""Persistence tests: disposable MariaDB only."""
import os
import unittest
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.engine import make_url

@unittest.skipUnless(os.getenv('PIJAR_DISPOSABLE_DB') == 'yes', 'Disposable database required')
class ProductionPersistenceTests(unittest.TestCase):
    def setUp(self):
        from flask import Flask
        from models import db, KategoriPJU, Wilayah
        uri = os.environ['PIJAR_TEST_DB_URI']
        if make_url(uri).database != 'pijar_bulk_test':
            raise RuntimeError('Only pijar_bulk_test allowed')
        self.app = Flask(__name__)
        self.app.config.update(SQLALCHEMY_DATABASE_URI=uri, SQLALCHEMY_TRACK_MODIFICATIONS=False)
        db.init_app(self.app)
        self.ctx = self.app.app_context(); self.ctx.push(); self.db = db
        self.addCleanup(self.cleanup)
        db.drop_all(); db.create_all()
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE aset_pju MODIFY tahun_pemasangan YEAR NULL, MODIFY tinggi_meter DECIMAL(4,1) NULL'))
            conn.execute(text("ALTER TABLE lampu MODIFY jenis_lampu VARCHAR(50) NOT NULL, MODIFY merk VARCHAR(100) NULL, MODIFY tahun_pasang YEAR NULL, MODIFY status_lampu ENUM('Menyala','Mati','Redup','Rusak') NOT NULL DEFAULT 'Menyala'"))
        db.session.add(KategoriPJU(id=1, kode='PJUP', nama='Uji', aktif=True))
        db.session.add(Wilayah(id_wilayah=1, kode_wilayah='UH2', nama_kelurahan='Uji', nama_kemantren='Uji'))
        db.session.commit()

    def cleanup(self):
        self.db.session.rollback(); self.db.session.remove()
        self.db.drop_all(); self.ctx.pop()

    def roundtrip(self, status, brand):
        from aset_bulk_service import ASSET, LAMP, validate, persist
        from models import AsetPJU, Lampu
        asset = dict(zip(ASSET, ['PJUP-UH2-26-001','PJUP','UH2','Sektor 1','2026','Uji','-7.8','110.37','Jalan Kota','','Besi','8.2','Menyala']))
        lamp = dict(zip(LAMP, ['PJUP-UH2-26-001','LED','60',brand,'2026',status]))
        assets, lamps = validate([(2,asset)],[(2,lamp)],{'PJUP':1},{'UH2':1},set())
        self.assertEqual(persist(assets,lamps), {'total_aset':1,'total_lampu':1})
        self.db.session.remove()
        saved = Lampu.query.one()
        self.assertEqual(saved.status_lampu, status)
        self.assertEqual(saved.merk, brand)
        self.assertEqual(saved.tahun_pasang, 2026)
        self.assertEqual(saved.to_dict()['status_lampu'], status)
        aset = AsetPJU.query.one()
        self.assertEqual(saved.id_aset, aset.id_aset)
        self.assertEqual(aset.tahun_pemasangan, 2026)
        self.assertEqual(aset.tinggi_meter, Decimal('8.2'))
        return saved

    def test_redup_roundtrip(self):
        self.roundtrip('Redup', 'Uji')

    def test_brand_100_roundtrip(self):
        self.assertEqual(len(self.roundtrip('Menyala', 'M'*100).merk), 100)

    def test_redup_and_brand_100_roundtrip(self):
        self.roundtrip('Redup', 'M'*100)

    def test_production_column_definitions(self):
        rows = self.db.session.execute(text("SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND ((TABLE_NAME='lampu' AND COLUMN_NAME IN ('status_lampu','merk','jenis_lampu','tahun_pasang')) OR (TABLE_NAME='aset_pju' AND COLUMN_NAME IN ('tahun_pemasangan','tinggi_meter')))"))
        actual = {(r[0],r[1]): (r[2].lower(),r[3]) for r in rows}
        self.assertEqual(actual[('lampu','merk')], ('varchar(100)','YES'))
        self.assertEqual(actual[('lampu','jenis_lampu')], ('varchar(50)','NO'))
        self.assertIn('redup', actual[('lampu','status_lampu')][0])
        self.assertNotIn('diganti', actual[('lampu','status_lampu')][0])
        self.assertEqual(actual[('aset_pju','tinggi_meter')][0], 'decimal(4,1)')
        for key in [('aset_pju','tahun_pemasangan'),('lampu','tahun_pasang')]:
            self.assertTrue(actual[key][0].startswith('year'))

if __name__ == '__main__':
    unittest.main()
