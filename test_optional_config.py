import shutil
import tempfile
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
import service,release_check

class OptionalConfigTests(unittest.TestCase):
    def test_missing_optional_config_allows_startup_and_calculation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'app'
            shutil.copytree(service.ROOT,root,ignore=shutil.ignore_patterns('__pycache__'))
            shutil.rmtree(root/'.streamlit')
            self.assertEqual(release_check.problems(root,'M23-PY-13'),[])
            at=AppTest.from_file(str(root/'app.py'),default_timeout=45).run()
            self.assertFalse(at.exception)
            self.assertFalse(at.error)
            at.button(key='calculate').click().run()
            self.assertFalse(at.exception)
            self.assertFalse(at.error)
            self.assertEqual(at.metric[0].value,'18')

    def test_required_code_remains_checked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'app'
            shutil.copytree(service.ROOT,root,ignore=shutil.ignore_patterns('__pycache__'))
            (root/'engine/frame.py').unlink()
            self.assertTrue(any('engine/frame.py' in x for x in release_check.problems(root,'M23-PY-13')))
            (root/'ultimate_ui.py').write_text('def show(p,profiles,gid,basis=None):\n    pass\n')
            self.assertTrue(any('ultimate_ui.py' in x for x in release_check.problems(root,'M23-PY-13')))
            self.assertTrue(release_check.problems(root,'OTHER_VERSION'))

if __name__=='__main__':unittest.main()
