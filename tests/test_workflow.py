"""Exercise the full local CLI workflow without network or a running Hermes model."""
import argparse
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from test_plugin import load_plugin

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.original=os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"]=self.temp.name
        self.home=Path(self.temp.name)
        self.skills=self.home/"skills"/"android-re"
        self.skills.mkdir(parents=True)
        (self.skills/"SKILL.md").write_text(
            "---\nname: android-re\ndescription: Inspect Android APK decompilation\n"
            "metadata:\n  hermes:\n    tags: [apk, android, jadx]\n---\n"
            "## When to Use\nDecompile APK files for analysis.\n",encoding="utf-8")
        self.plugin=load_plugin()

    def tearDown(self):
        if self.original is None:
            os.environ.pop("HERMES_HOME",None)
        else:
            os.environ["HERMES_HOME"]=self.original
        self.temp.cleanup()

    def test_rebuild_audit_review_enable(self):
        from skillsense_test.store import open_db,rows,publish_index,stage
        from skillsense_test.routing import clear_cache,hint
        from skillsense_test.store import save_native_snapshot
        self.assertIn("Rebuilt",self.plugin._rebuild(argparse.Namespace(roots=None)))
        self.assertIn("1 skills",self.plugin._status())
        dry=self.plugin._clean(argparse.Namespace(roots=None,model="none",dry_run=True,
                                                   force=False,endpoint=None,model_id=None))
        self.assertIn("no files or database changed",dry)
        conn=open_db()
        try:
            row=rows(conn)[0]
            self.assertTrue(stage(conn,row["id"],row["source_hash"],
                             {"description":"APK decompilation with jadx","tags":["dex"]}))
        finally:
            conn.close()
        self.assertIn("android-re",self.plugin._review(
            argparse.Namespace(review_action="list",skill=None)))
        self.assertIn("Approved",self.plugin._review(
            argparse.Namespace(review_action="approve",skill="android-re")))
        from unittest.mock import patch
        save_native_snapshot({"android-re":"Inspect Android APK decompilation"})
        self.assertIn("enabled",self.plugin._configure(argparse.Namespace(action="enable")))
        clear_cache()
        self.assertIn("android-re",hint("decompile an Android APK with jadx")["context"])
        self.assertIn("disabled",self.plugin._configure(argparse.Namespace(action="disable")))

    def test_successful_metadata_audit_refreshes_native_snapshot(self):
        from unittest.mock import patch
        from skillsense_test.store import read_native_snapshot
        available={"android-re":"Inspect Android APK decompilation"}
        with patch("skillsense_test.eligibility.native_skill_allowlist",
                   return_value=available):
            result=self.plugin._clean(argparse.Namespace(
                roots=None, model="none",dry_run=False,force=False,
                endpoint=None,model_id=None))
        self.assertIn("Audit completed",result)
        self.assertEqual(read_native_snapshot(),available)

    def test_stale_review_immediately_removes_old_approved_metadata(self):
        from skillsense_test.store import open_db, rows, stage, publish_index, read_index
        from skillsense_test.routing import clear_cache
        # First publish a known approved alias and verify it reaches the index.
        self.plugin._rebuild(argparse.Namespace(roots=None))
        conn = open_db()
        try:
            original = rows(conn)[0]
            self.assertTrue(stage(conn,original["id"],original["source_hash"],
                                  {"description":"Inspect Android APK decompilation",
                                   "aliases":["smoke test alias"]}))
        finally:
            conn.close()
        self.assertIn("Approved",self.plugin._review(
            argparse.Namespace(review_action="approve",skill="android-re")))
        self.assertIn("smoke test alias",read_index()[0]["aliases"])
        # Stage another revision before the underlying source changes.
        conn = open_db()
        try:
            same = rows(conn)[0]
            self.assertTrue(stage(conn,same["id"],same["source_hash"],
                                  {"description":"Updated APK audit metadata"}))
        finally:
            conn.close()
        source=self.skills/"SKILL.md"
        source.write_text(source.read_text(encoding="utf-8")+"\\nChanged after audit.\\n",
                          encoding="utf-8")
        message=self.plugin._review(
            argparse.Namespace(review_action="approve",skill="android-re"))
        self.assertIn("stale",message)
        self.assertEqual(read_index()[0]["aliases"],[])
        conn=open_db()
        try:
            current=rows(conn)[0]
            self.assertEqual(current["status"],"stale")
            self.assertIsNone(current["approved"])
        finally:
            conn.close()


    def test_stale_rejection_revokes_prior_alias_in_published_index(self):
        from skillsense_test.store import open_db, rows, stage, read_index
        self.plugin._rebuild(argparse.Namespace(roots=None))
        conn=open_db()
        try:
            row=rows(conn)[0]
            self.assertTrue(stage(conn,row["id"],row["source_hash"],
                                  {"description":"Inspect Android APK decompilation",
                                   "aliases":["previous alias"]}))
        finally:
            conn.close()
        self.assertIn("Approved",self.plugin._review(
            argparse.Namespace(review_action="approve",skill="android-re")))
        self.assertEqual(read_index()[0]["aliases"],["previous alias"])
        conn=open_db()
        try:
            row=rows(conn)[0]
            self.assertTrue(stage(conn,row["id"],row["source_hash"],
                                  {"description":"Replacement review proposal"}))
        finally:
            conn.close()
        source=self.skills/"SKILL.md"
        source.write_text(source.read_text(encoding="utf-8")+"\nEdited since proposal.\n",
                          encoding="utf-8")
        result=self.plugin._review(
            argparse.Namespace(review_action="reject",skill="android-re"))
        self.assertIn("stale",result)
        self.assertEqual(read_index()[0]["aliases"],[])

    def test_malicious_remote_url_fails_before_scan(self):
        from skillsense_test.local_model import LocalOnlyError
        with self.assertRaises(LocalOnlyError):
            self.plugin._clean(argparse.Namespace(
                roots=None,model="aux",dry_run=False,force=False,
                endpoint="https://openrouter.ai/v1/chat/completions",model_id="remote"))

if __name__=="__main__":
    unittest.main()

    def test_opt_in_empty_rebuild_reconciles_only_requested_root(self):
        from skillsense_test.store import open_db, rows, read_index
        from unittest.mock import patch
        primary = self.home / "skills"
        secondary = self.home / "other-skills"
        other = secondary / "secondary"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text(
            "---\nname: secondary\ndescription: Manage secondary workflows\n---\n",
            encoding="utf-8")
        with patch("skillsense_test.eligibility.native_skill_allowlist",
                   return_value={"secondary":"Manage secondary workflows"}):
            self.plugin._rebuild(argparse.Namespace(roots=[str(primary),str(secondary)]))
            conn=open_db()
            try:
                self.assertEqual({row["name"] for row in rows(conn)},
                                 {"android-re","secondary"})
            finally:
                conn.close()

            source = self.skills / "SKILL.md"
            source.unlink()
            with self.assertRaisesRegex(ValueError,"--allow-empty"):
                self.plugin._rebuild(argparse.Namespace(roots=[str(primary)]))
            self.assertEqual({row["name"] for row in read_index()},
                             {"android-re","secondary"})

            result = self.plugin._rebuild(argparse.Namespace(
                roots=[str(primary)], allow_empty=True))
            self.assertIn("0 skills", result)
            self.assertEqual({row["name"] for row in read_index()}, {"secondary"})
            conn=open_db()
            try:
                self.assertEqual({row["name"] for row in rows(conn)}, {"secondary"})
            finally:
                conn.close()
        self.assertTrue((other / "SKILL.md").is_file())
