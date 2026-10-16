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
        self.assertIn("enabled",self.plugin._configure(argparse.Namespace(action="enable")))
        clear_cache()
        from unittest.mock import patch
        with patch("skillsense_test.routing.native_skill_allowlist",
                   return_value={"android-re":"Inspect Android APK decompilation"}):
            self.assertIn("android-re",hint("decompile an Android APK with jadx")["context"])
        self.assertIn("disabled",self.plugin._configure(argparse.Namespace(action="disable")))

    def test_malicious_remote_url_fails_before_scan(self):
        from skillsense_test.local_model import LocalOnlyError
        with self.assertRaises(LocalOnlyError):
            self.plugin._clean(argparse.Namespace(
                roots=None,model="aux",dry_run=False,force=False,
                endpoint="https://openrouter.ai/v1/chat/completions",model_id="remote"))

if __name__=="__main__":
    unittest.main()
