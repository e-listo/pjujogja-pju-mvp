import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'deploy-production.sh'

class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root/'source'; self.src.mkdir(); (self.src/'a.js').write_text('source')
        self.dst = self.root/'target'
    def run_copy(self):
        return subprocess.run(['bash','-c','source "$1"; copy_directory_files "$2" "$3"','test',str(SCRIPT),str(self.src),str(self.dst)],capture_output=True,text=True)
    def test_same_directory_symlink(self):
        self.dst.symlink_to(self.src, target_is_directory=True)
        r=self.run_copy(); self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('SKIP same directory',r.stdout); self.assertTrue(self.dst.is_symlink())
        self.assertEqual((self.src/'a.js').read_text(),'source')
    def test_real_destination(self):
        r=self.run_copy(); self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual((self.dst/'a.js').read_text(),'source')
    def test_external_symlink_rejected(self):
        other=self.root/'other'; other.mkdir(); self.dst.symlink_to(other,target_is_directory=True)
        self.assertNotEqual(self.run_copy().returncode,0); self.assertFalse((other/'a.js').exists())
    def test_dangling_symlink_rejected(self):
        self.dst.symlink_to(self.root/'missing'); self.assertNotEqual(self.run_copy().returncode,0)
    def test_destination_file_symlink_rejected(self):
        self.dst.mkdir(); secret=self.root/'secret'; secret.write_text('keep')
        (self.dst/'a.js').symlink_to(secret)
        self.assertNotEqual(self.run_copy().returncode,0); self.assertEqual(secret.read_text(),'keep')
    def fixture(self):
        repo=self.root/'repo'; repo.mkdir(); shutil.copyfile(SCRIPT,repo/'deploy-production.sh')
        for name in ('app.py','auth_routes.py','config.py','models.py','passenger_wsgi.py','aset_bulk_service.py','aset_bulk_routes.py'):
            (repo/name).write_text('value = 1')
        (repo/'requirements.txt').write_text('')
        js=repo/'frontend/admin/js'; js.mkdir(parents=True)
        for name in ('aset-bulk.js','detail-deeplink.js'): (js/name).write_text('')
        (repo/'frontend/admin/aset.html').write_text('<html></html>')
        field=repo/'frontend/lapangan'; field.mkdir(); (field/'index.html').write_text('<html></html>')
        (repo/'js').symlink_to(js,target_is_directory=True); (repo/'lapangan').symlink_to(field,target_is_directory=True)
        api=self.root/'api'; api.mkdir(); return repo,api
    def dryrun(self,repo,api):
        return subprocess.run(['bash',str(repo/'deploy-production.sh'),'--dry-run'],env=dict(os.environ,HOME=str(self.root),PIJAR_API_DIR=str(api),PIJAR_PYTHON=sys.executable),capture_output=True,text=True)
    def test_complete_symlink_preflight_read_only(self):
        repo,api=self.fixture(); r=self.dryrun(repo,api)
        self.assertEqual(r.returncode,0,r.stderr); self.assertFalse((repo/'aset.html').exists())
        self.assertEqual(list(api.iterdir()),[])
    def test_missing_source_fails_before_write(self):
        repo,api=self.fixture(); (repo/'aset_bulk_routes.py').unlink(); r=self.dryrun(repo,api)
        self.assertNotEqual(r.returncode,0); self.assertEqual(list(api.iterdir()),[])

if __name__ == '__main__': unittest.main()
