"""Regression contract from production DDL supplied on 2026-10-07."""
import unittest
from decimal import Decimal
from aset_bulk_service import ASSET, LAMP, BatchError, validate


def check(asset_changes=None, lamp_changes=None):
    asset = dict(zip(ASSET, [
        'PJUP-UH2-26-001', 'PJUP', 'UH2', 'Sektor 1', '2026',
        'Lokasi uji', '-7.8', '110.37', 'Jalan Kota', '',
        'Besi', '8', 'Menyala',
    ]))
    lamp = dict(zip(LAMP, [
        'PJUP-UH2-26-001', 'LED', '60', 'Uji', '2026', 'Menyala',
    ]))
    asset.update(asset_changes or {})
    lamp.update(lamp_changes or {})
    return validate([(2, asset)], [(2, lamp)], {'PJUP': 1}, {'UH2': 1}, set())


class ProductionValidationTests(unittest.TestCase):
    def test_production_lamp_statuses(self):
        for status in ('Menyala', 'Mati', 'Redup', 'Rusak'):
            with self.subTest(status=status):
                self.assertEqual(check(lamp_changes={'status_lampu': status})[1][0]['status_lampu'], status)

    def test_diganti_rejected(self):
        with self.assertRaises(BatchError):
            check(lamp_changes={'status_lampu': 'Diganti'})

    def test_lamp_type_required(self):
        for value in ('', ' '):
            with self.subTest(value=value), self.assertRaises(BatchError):
                check(lamp_changes={'jenis_lampu': value})

    def test_lamp_brand_100_characters(self):
        self.assertEqual(check(lamp_changes={'merk': 'M' * 100})[1][0]['merk'], 'M' * 100)
        with self.assertRaises(BatchError):
            check(lamp_changes={'merk': 'M' * 101})

    def test_lamp_type_length(self):
        self.assertEqual(check(lamp_changes={'jenis_lampu': 'L' * 50})[1][0]['jenis_lampu'], 'L' * 50)
        with self.assertRaises(BatchError):
            check(lamp_changes={'jenis_lampu': 'L' * 51})

    def test_year_boundaries(self):
        for year in (1901, 2155):
            code = f'PJUP-UH2-{year % 100:02d}-001'
            with self.subTest(year=year):
                assets, lamps = check(
                    {'kode_aset': code, 'tahun_pemasangan': str(year)},
                    {'kode_aset': code, 'tahun_pasang': str(year)},
                )
                self.assertEqual(assets[0]['tahun_pemasangan'], year)
                self.assertEqual(lamps[0]['tahun_pasang'], year)

    def test_years_outside_production_range(self):
        for year in (0, 1, 1900, 2156, 9999):
            code = f'PJUP-UH2-{year % 100:02d}-001'
            with self.subTest(field='asset', year=year), self.assertRaises(BatchError):
                check({'kode_aset': code, 'tahun_pemasangan': str(year)}, {'kode_aset': code})
            with self.subTest(field='lamp', year=year), self.assertRaises(BatchError):
                check(lamp_changes={'tahun_pasang': str(year)})

    def test_unknown_years_are_null(self):
        assets, lamps = check({'tahun_pemasangan': ''}, {'tahun_pasang': ''})
        self.assertIsNone(assets[0]['tahun_pemasangan'])
        self.assertIsNone(lamps[0]['tahun_pasang'])

    def test_height_one_decimal_and_upper_boundary(self):
        for value in ('0.1', '8.2', '999.9'):
            with self.subTest(value=value):
                self.assertEqual(check({'tinggi_meter': value})[0][0]['tinggi_meter'], Decimal(value))

    def test_height_not_silently_rounded(self):
        for value in ('8.25', '999.99', '1000', '-1'):
            with self.subTest(value=value), self.assertRaises(BatchError):
                check({'tinggi_meter': value})


if __name__ == '__main__':
    unittest.main()
