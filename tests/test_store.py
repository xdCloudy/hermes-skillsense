import json
import hashlib
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
                source = root / "SKILL.md"
                source.write_text("original skill body",encoding="utf-8")
                original=Skill("id","android","APK reverse engineering",("apk",),
                               ("Inspect Android apps",),str(source),
                               hashlib.sha256(source.read_bytes()).hexdigest())
                sync(conn,[original]); publish_index(conn,root)
                self.assertEqual(len(read_index(root)),1)
                self.assertTrue(stage(conn,"id",original.sha256,
                                 {"description":"Decompile APK apps","tags":["jadx"]}))
                self.assertFalse(stage(conn,"id","other",
                                 {"description":"Bad hash","tags":["bad"]}))
                self.assertTrue(decide(conn,"id",True))
                publish_index(conn,root)
                self.assertIn("jadx",read_index(root)[0]["tags"])
                source.write_text("changed skill body",encoding="utf-8")
                changed=Skill("id","android","New content",("apk",),(),str(source),hashlib.sha256(source.read_bytes()).hexdigest())
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

    def test_root_scoped_sync_preserves_other_root_metadata(self):
        from skillsense_test.catalog import Skill
        from skillsense_test.store import open_db, sync, rows
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp); a=base/"a";b=base/"b";a.mkdir();b.mkdir()
            file_a=a/"SKILL.md";file_b=b/"SKILL.md"
            file_a.write_text("aaa");file_b.write_text("bbb")
            sa=Skill("A","a","A",(),(),str(file_a),hashlib.sha256(file_a.read_bytes()).hexdigest())
            sb=Skill("B","b","B",(),(),str(file_b),hashlib.sha256(file_b.read_bytes()).hexdigest())
            conn=open_db(base/"data")
            try:
                sync(conn,[sa,sb],roots=[a,b])
                sync(conn,[sa],roots=[a])
                self.assertEqual({r["id"] for r in rows(conn)},{"A","B"})
                file_a.unlink()
                sync(conn,[],roots=[a])
                self.assertEqual({r["id"] for r in rows(conn)},{"B"})
            finally:
                conn.close()

    def test_reject_stale_approval_after_file_changed(self):
        from skillsense_test.catalog import Skill
        from skillsense_test.store import open_db, sync, rows, stage, decide
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); file=root/"SKILL.md";file.write_text("initial")
            key=hashlib.sha256(file.read_bytes()).hexdigest()
            item=Skill("A","a","A",(),(),str(file),key)
            conn=open_db(root/"db")
            try:
                sync(conn,[item],roots=[root])
                self.assertTrue(stage(conn,"A",key,{"description":"Validated metadata"}))
                file.write_text("edited after audit")
                self.assertFalse(decide(conn,"A",True))
                r=rows(conn)[0]
                self.assertEqual(r["status"],"stale")
                self.assertIsNone(r["approved"])
                self.assertIsNone(r["pending"])
            finally:
                conn.close()
