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
    def bash(self, body, cwd=None, *args):
        return subprocess.run(['bash','-c','source "$1"; shift; '+body,'test',str(SCRIPT),*args],cwd=cwd,capture_output=True,text=True)
    def run_copy(self):
        return self.bash('copy_directory_files "$1" "$2"',None,str(self.src),str(self.dst))
    def test_same_directory_symlink(self):
        self.dst.symlink_to(self.src, target_is_directory=True)
        r=self.run_copy(); self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('SKIP same directory',r.stdout); self.assertTrue(self.dst.is_symlink())
        self.assertEqual((self.src/'a.js').read_text(),'source')
    def test_same_directory_with_subdirectory_is_not_rejected(self):
        (self.src/'nested').mkdir(); self.dst.symlink_to(self.src, target_is_directory=True)
        r=self.run_copy(); self.assertEqual(r.returncode,0,r.stderr)
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
    def fixture(self, link_pages=True):
        repo=self.root/'repo'; repo.mkdir(); shutil.copyfile(SCRIPT,repo/'deploy-production.sh')
        for name in ('app.py','auth_routes.py','config.py','models.py','passenger_wsgi.py','aset_bulk_service.py','aset_bulk_routes.py'):
            (repo/name).write_text('value = "\u2014"\n', encoding='utf-8')
        (repo/'requirements.txt').write_text('')
        js=repo/'frontend/admin/js'; js.mkdir(parents=True)
        for name in ('aset-bulk.js','detail-deeplink.js'): (js/name).write_text('')
        page=repo/'frontend/admin/aset.html'
        page.write_text('<script src="js/detail-deeplink.js"></script>')
        field=repo/'frontend/lapangan'; field.mkdir(); (field/'index.html').write_text('<html></html>')
        (repo/'js').symlink_to(js,target_is_directory=True); (repo/'lapangan').symlink_to(field,target_is_directory=True)
        if link_pages: (repo/'aset.html').symlink_to('frontend/admin/aset.html')
        api=self.root/'api'; api.mkdir(); return repo,api
    def dryrun(self,repo,api):
        return subprocess.run(['bash',str(repo/'deploy-production.sh'),'--dry-run'],env=dict(os.environ,HOME=str(self.root),PIJAR_API_DIR=str(api),PIJAR_PYTHON=sys.executable),capture_output=True,text=True)
    def test_server_layout_with_symlinked_pages_passes_read_only(self):
        repo,api=self.fixture(); before=(repo/'frontend/admin/aset.html').read_text(); r=self.dryrun(repo,api)
        self.assertEqual(r.returncode,0,r.stderr); self.assertTrue((repo/'aset.html').is_symlink())
        self.assertEqual((repo/'frontend/admin/aset.html').read_text(),before); self.assertEqual(list(api.iterdir()),[])
    def test_regular_root_page_passes_read_only(self):
        repo,api=self.fixture(False); (repo/'aset.html').write_text('old'); r=self.dryrun(repo,api)
        self.assertEqual(r.returncode,0,r.stderr); self.assertEqual((repo/'aset.html').read_text(),'old')
    def test_external_page_symlink_rejected(self):
        repo,api=self.fixture(False); other=self.root/'other.html'; other.write_text('keep'); (repo/'aset.html').symlink_to(other)
        r=self.dryrun(repo,api); self.assertNotEqual(r.returncode,0); self.assertEqual(other.read_text(),'keep'); self.assertEqual(list(api.iterdir()),[])
    def test_dangling_page_symlink_rejected(self):
        repo,api=self.fixture(False); (repo/'aset.html').symlink_to(self.root/'missing.html')
        self.assertNotEqual(self.dryrun(repo,api).returncode,0); self.assertEqual(list(api.iterdir()),[])
    def test_copy_pages_skips_symlinked_page(self):
        repo,api=self.fixture(); before=(repo/'frontend/admin/aset.html').read_text()
        r=self.bash('copy_pages frontend/admin/aset.html',repo); self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('SKIP same file',r.stdout); self.assertTrue((repo/'aset.html').is_symlink()); self.assertEqual((repo/'frontend/admin/aset.html').read_text(),before)
    def test_copy_pages_updates_regular_page(self):
        repo,api=self.fixture(False); (repo/'aset.html').write_text('old')
        r=self.bash('copy_pages frontend/admin/aset.html',repo); self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual((repo/'aset.html').read_text(),(repo/'frontend/admin/aset.html').read_text())
    def test_stamp_does_not_modify_tracked_source_through_symlink(self):
        repo,api=self.fixture(); before=(repo/'frontend/admin/aset.html').read_text()
        r=self.bash('stamp_html_versions "$1" "$2" abc1234',None,sys.executable,str(repo)); self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual((repo/'frontend/admin/aset.html').read_text(),before)
    def test_stamp_updates_regular_copied_page(self):
        repo,api=self.fixture(False); shutil.copyfile(repo/'frontend/admin/aset.html',repo/'aset.html')
        r=self.bash('stamp_html_versions "$1" "$2" abc1234',None,sys.executable,str(repo)); self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('js/detail-deeplink.js?v=abc1234',(repo/'aset.html').read_text())
        self.assertNotIn('?v=',(repo/'frontend/admin/aset.html').read_text())
    def test_missing_source_fails_before_write(self):
        repo,api=self.fixture(); (repo/'aset_bulk_routes.py').unlink(); r=self.dryrun(repo,api)
        self.assertNotEqual(r.returncode,0); self.assertEqual(list(api.iterdir()),[])

if __name__ == '__main__': unittest.main()
