import json
import hashlib
import os
import stat
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

    def test_reject_pending_stale_source_clears_previous_approval(self):
        from skillsense_test.catalog import Skill
        from skillsense_test.store import open_db, sync, rows, stage, decide
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);file=root/"SKILL.md";file.write_text("original",encoding="utf-8")
            digest=hashlib.sha256(file.read_bytes()).hexdigest()
            record=Skill("A","a","Original capability",(),(),str(file),digest)
            conn=open_db(root/"db")
            try:
                sync(conn,[record],roots=[root])
                self.assertTrue(stage(conn,"A",digest,{"description":"First revision"}))
                self.assertTrue(decide(conn,"A",True))
                self.assertEqual(rows(conn)[0]["approved"]["description"],"First revision")
                self.assertTrue(stage(conn,"A",digest,{"description":"Second revision"}))
                file.write_text("changed after proposal",encoding="utf-8")
                self.assertFalse(decide(conn,"A",False))
                row=rows(conn)[0]
                self.assertEqual(row["status"],"stale")
                self.assertIsNone(row["approved"])
                self.assertIsNone(row["pending"])
            finally:
                conn.close()

    def test_malformed_persisted_index_reverts_to_native_only(self):
        from skillsense_test.store import read_index
        from skillsense_test.eligibility import compose_native_records
        from skillsense_test.routing import Router
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            index = home / "index.json"
            native = {"android-re": "Inspect Android APK decompilation"}
            valid = {
                "id": "profile::android-re", "name": "android-re",
                "source_description": native["android-re"],
                "description": "Inspect Android APK decompilation",
                "tags": ["apk"], "aliases": ["malicious-alias"],
                "intents": [], "negative_intents": [],
            }
            for bad in (
                dict(valid, aliases="not a list"),
                dict(valid, description={"unexpected": "nested mapping"}),
                dict(valid, id=123),
                dict(valid, name="bad name with spaces"),
                [valid],
            ):
                with self.subTest(bad=bad):
                    index.write_text(json.dumps({"schema": 1, "skills": [bad]}),
                                     encoding="utf-8")
                    self.assertEqual(read_index(home), [])
                    fallback = compose_native_records(read_index(home), native)
                    self.assertEqual(fallback[0]["aliases"], [])
                    self.assertIn("android-re", Router(fallback).suggest("android-re APK"))

    def test_duplicate_and_oversized_indexes_abstain_instead_of_truncating(self):
        from skillsense_test.store import read_index
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            index = home / "index.json"
            row = {
                "id": "one", "name": "skill", "source_description": "A",
                "description": "A", "tags": [], "aliases": [],
                "intents": [], "negative_intents": [],
            }
            index.write_text(json.dumps({"schema": 1, "skills": [row, row]}),
                             encoding="utf-8")
            self.assertEqual(read_index(home), [])
            index.write_text(json.dumps({"schema": 1,
                                         "skills": [dict(row, id=str(i)) for i in range(2501)]}),
                             encoding="utf-8")
            self.assertEqual(read_index(home), [])

    def test_sync_dirties_old_index_before_database_source_revisions(self):
        from skillsense_test.catalog import Skill
        from skillsense_test.store import (open_db, sync, stage, decide,
                                          publish_index, read_index_status, rows)
        from skillsense_test.eligibility import compose_native_records
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            source = home / "SKILL.md"
            source.write_text("original", encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            native = {"android-re": "Inspect APKs"}
            conn = open_db(home)
            try:
                original = Skill("one", "android-re", "Inspect APKs", (), (),
                                 str(source), digest)
                sync(conn, [original])
                stage(conn, "one", digest,
                      {"description": "Inspect APKs", "aliases": ["old unique alias"]})
                self.assertTrue(decide(conn, "one", True))
                publish_index(conn, home)
                self.assertTrue(read_index_status(home)[1])
                self.assertEqual(read_index_status(home)[0][0]["aliases"], ["old unique alias"])

                source.write_text("changed", encoding="utf-8")
                replacement = Skill("one", "android-re", "Inspect APKs", (), (),
                                    str(source), hashlib.sha256(source.read_bytes()).hexdigest())
                # Simulate a process crash/failed publish after the DB update.
                sync(conn, [replacement])
                records, valid = read_index_status(home)
                self.assertFalse(valid)
                self.assertEqual(records, [])
                self.assertIsNone(rows(conn)[0]["approved"])
                fallback = compose_native_records(records, native)
                self.assertEqual(fallback[0]["aliases"], [])
                publish_index(conn, home)
                self.assertTrue(read_index_status(home)[1])
                self.assertEqual(read_index_status(home)[0][0]["aliases"], [])
            finally:
                conn.close()

    def test_unpublished_rejection_cannot_leave_old_alias_available(self):
        from skillsense_test.catalog import Skill
        from skillsense_test.store import (open_db, sync, stage, decide,
                                          publish_index, read_index_status)
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            source = home / "SKILL.md"
            source.write_text("same file", encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            conn = open_db(home)
            try:
                skill = Skill("one", "android-re", "Inspect APKs", (), (),
                              str(source), digest)
                sync(conn, [skill])
                stage(conn, "one", digest,
                      {"description": "Inspect APKs", "aliases": ["previous alias"]})
                self.assertTrue(decide(conn, "one", True))
                publish_index(conn, home)
                self.assertTrue(read_index_status(home)[1])
                stage(conn, "one", digest,
                      {"description": "New proposal"})
                self.assertTrue(decide(conn, "one", False))
                # No publish_index: a crash must leave no valid stale index.
                self.assertFalse(read_index_status(home)[1])
                publish_index(conn, home)
                self.assertTrue(read_index_status(home)[1])
            finally:
                conn.close()

    @unittest.skipUnless(os.name == "posix", "POSIX ownership modes only")
    def test_sqlite_sidecar_created_private_even_with_permissive_umask(self):
        from skillsense_test.store import open_db
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "skillsense"
            old_umask = os.umask(0)
            try:
                conn = open_db(root)
                conn.close()
            finally:
                os.umask(old_umask)
            self.assertEqual(stat.S_IMODE(root.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE((root / "data.db").stat().st_mode), 0o600)

            # An older version may have created a broadly readable DB.
            os.chmod(root / "data.db", 0o666)
            conn = open_db(root)
            conn.close()
            self.assertEqual(stat.S_IMODE((root / "data.db").stat().st_mode), 0o600)

    @unittest.skipUnless(os.name == "posix" and hasattr(os, "O_NOFOLLOW"),
                         "O_NOFOLLOW is unavailable")
    def test_database_path_symlink_is_rejected(self):
        from skillsense_test.store import open_db
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "skillsense"
            root.mkdir()
            protected = Path(temp) / "external.db"
            protected.write_bytes(b"do not overwrite")
            (root / "data.db").symlink_to(protected)
            with self.assertRaises(OSError):
                open_db(root)
            self.assertEqual(protected.read_bytes(), b"do not overwrite")
