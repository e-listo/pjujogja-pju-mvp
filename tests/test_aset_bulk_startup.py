import os
import unittest
from unittest.mock import patch

@unittest.skipUnless(os.getenv('PIJAR_DISPOSABLE_DB')=='yes','Database uji diperlukan')
class WSGIStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy.engine import make_url
        uri=os.environ['PIJAR_TEST_DB_URI']
        if make_url(uri).database!='pijar_bulk_test':
            raise RuntimeError('Database uji wajib pijar_bulk_test')
        cls.environ=patch.dict(os.environ,{'DATABASE_URL':uri,'JWT_SECRET':'ci-startup-only-not-production-secret-123456','SECRET_KEY':'ci-startup-only-not-production-secret-123456'})
        cls.environ.start();cls.addClassCleanup(cls.environ.stop)
        from passenger_wsgi import application
        cls.app=application;cls.client=application.test_client()
    def test_database_isolation(self):
        from sqlalchemy.engine import make_url
        self.assertEqual(make_url(self.app.config['SQLALCHEMY_DATABASE_URI']).database,'pijar_bulk_test')
    def test_registered_routes(self):
        routes={rule.rule for rule in self.app.url_map.iter_rules()}
        self.assertTrue({'/api/aset/import/template','/api/aset/import/preview','/api/aset/import/commit'}.issubset(routes))
    def test_health(self):
        r=self.client.get('/api/health')
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.get_json()['success'])
    def test_import_requires_jwt(self):
        self.assertEqual(self.client.get('/api/aset/import/template').status_code,401)
        self.assertEqual(self.client.post('/api/aset/import/preview').status_code,401)
        self.assertEqual(self.client.post('/api/aset/import/commit').status_code,401)
