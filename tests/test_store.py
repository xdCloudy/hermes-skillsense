import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_catalog import module
class StoreTests(unittest.TestCase):
    def setUp(self):
        module()

    def test_transactional_index_review_and_invalidation(self):
        from skillsense_test.catalog import Skill
        from skillsense_test.store import open_db,sync,stage,decide,publish_index,read_index
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            conn=open_db(root)
            try:
                original=Skill("id","android","APK reverse engineering",("apk",),
                               ("Inspect Android apps",),"a", "a"*64)
                sync(conn,[original]); publish_index(conn,root)
                self.assertEqual(len(read_index(root)),1)
                self.assertTrue(stage(conn,"id",original.sha256,
                                 {"description":"Decompile APK apps","tags":["jadx"]}))
                self.assertFalse(stage(conn,"id","other",
                                 {"description":"Bad hash","tags":["bad"]}))
                self.assertTrue(decide(conn,"id",True))
                publish_index(conn,root)
                self.assertIn("jadx",read_index(root)[0]["tags"])
                changed=Skill("id","android","New content",("apk",),(),"a","b"*64)
                sync(conn,[changed]);publish_index(conn,root)
                self.assertNotIn("jadx",read_index(root)[0]["tags"])
                self.assertEqual(read_index(root)[0]["description"],"New content")
            finally:
                conn.close()

    def test_corrupt_index_fails_safely(self):
        from skillsense_test.store import read_index
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp)/"index.json").write_text("corrupt",encoding="utf-8")
            self.assertEqual(read_index(Path(temp)),[])
