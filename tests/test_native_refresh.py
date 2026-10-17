"""Hermes-native availability refresh works without a SKILL.md directory."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_plugin import load_plugin

class NativeRefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.old=os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"]=self.temp.name
        self.plugin=load_plugin()

    def tearDown(self):
        if self.old is None:
            os.environ.pop("HERMES_HOME",None)
        else:
            os.environ["HERMES_HOME"]=self.old
        self.temp.cleanup()

    def test_plugin_only_catalogue_refresh_without_skill_files(self):
        from skillsense_test.store import read_native_snapshot,read_index
        from skillsense_test.routing import clear_cache,hint
        allowed={"plugin:diagram":"Generate architecture diagrams for networks"}
        with patch("skillsense_test.eligibility.native_skill_catalogue",
                   return_value=allowed):
            result=self.plugin._refresh_native()
        self.assertIn("1 skills",result)
        self.assertEqual(read_native_snapshot(),allowed)
        self.assertEqual(read_index(),[])
        clear_cache()
        self.assertIn("plugin:diagram",hint("plugin:diagram architecture networks")["context"])

    def test_confirmed_empty_native_result_revokes_existing_catalogue(self):
        from skillsense_test.store import save_native_snapshot, read_native_snapshot
        from skillsense_test.routing import clear_cache, hint
        before = {"existing": "Handle Git repository maintenance"}
        save_native_snapshot(before)
        with patch("skillsense_test.eligibility.native_skill_catalogue", return_value={}):
            result = self.plugin._refresh_native()
        self.assertIn("0 skills", result)
        self.assertIn("abstain", result)
        self.assertEqual(read_native_snapshot(), {})
        clear_cache()
        self.assertIsNone(hint("existing Git repository maintenance"))

    def test_failed_native_result_preserves_existing_catalogue(self):
        from skillsense_test.store import save_native_snapshot,read_native_snapshot
        before={"existing":"Handle Git repository maintenance"}
        save_native_snapshot(before)
        with patch("skillsense_test.eligibility.native_skill_catalogue",return_value=None):
            with self.assertRaisesRegex(RuntimeError,"existing snapshot preserved"):
                self.plugin._refresh_native()
        self.assertEqual(read_native_snapshot(),before)

    def test_rebuild_preserves_snapshot_when_host_lookup_fails(self):
        import argparse
        from skillsense_test.store import save_native_snapshot, read_native_snapshot
        existing = {"original": "Inspect known user workflows"}
        save_native_snapshot(existing)
        root = Path(self.temp.name) / "skills" / "sample"
        root.mkdir(parents=True)
        (root / "SKILL.md").write_text(
            "---\nname: sample\ndescription: Inspect sample workflows\n---\n",
            encoding="utf-8")
        with patch("skillsense_test.eligibility.native_skill_catalogue",
                   return_value=None):
            result = self.plugin._rebuild(argparse.Namespace(roots=[str(root.parent)]))
        self.assertIn("previous native snapshot retained", result)
        self.assertEqual(read_native_snapshot(), existing)

    def test_rebuild_verified_empty_revokes_previous_snapshot(self):
        import argparse
        from skillsense_test.store import save_native_snapshot, read_native_snapshot
        save_native_snapshot({"old-skill": "No longer installed"})
        root = Path(self.temp.name) / "skills" / "sample"
        root.mkdir(parents=True)
        (root / "SKILL.md").write_text(
            "---\nname: sample\ndescription: Inspect sample workflows\n---\n",
            encoding="utf-8")
        with patch("skillsense_test.eligibility.native_skill_catalogue",
                   return_value={}):
            result = self.plugin._rebuild(argparse.Namespace(roots=[str(root.parent)]))
        self.assertIn("Rebuilt index", result)
        self.assertEqual(read_native_snapshot(), {})

    def test_clean_preserves_snapshot_when_host_lookup_fails(self):
        import argparse
        from skillsense_test.store import save_native_snapshot, read_native_snapshot
        existing = {"old-skill": "Maintain local applications"}
        save_native_snapshot(existing)
        root = Path(self.temp.name) / "skills" / "sample"
        root.mkdir(parents=True)
        (root / "SKILL.md").write_text(
            "---\nname: sample\ndescription: Inspect sample workflows\n---\n",
            encoding="utf-8")
        with patch("skillsense_test.eligibility.native_skill_catalogue",
                   return_value=None):
            result = self.plugin._clean(argparse.Namespace(
                roots=[str(root.parent)], model="none", dry_run=False,
                force=False, endpoint=None, model_id=None))
        self.assertIn("previous native snapshot retained", result)
        self.assertEqual(read_native_snapshot(), existing)

    def test_clean_verified_empty_revokes_previous_snapshot(self):
        import argparse
        from skillsense_test.store import save_native_snapshot, read_native_snapshot
        save_native_snapshot({"old-skill": "No longer installed"})
        root = Path(self.temp.name) / "skills" / "sample"
        root.mkdir(parents=True)
        (root / "SKILL.md").write_text(
            "---\nname: sample\ndescription: Inspect sample workflows\n---\n",
            encoding="utf-8")
        with patch("skillsense_test.eligibility.native_skill_catalogue",
                   return_value={}):
            self.plugin._clean(argparse.Namespace(
                roots=[str(root.parent)], model="none", dry_run=False,
                force=False, endpoint=None, model_id=None))
        self.assertEqual(read_native_snapshot(), {})

    def test_refresh_does_not_remove_cached_approved_data(self):
        from skillsense_test.store import open_db,sync,rows
        from skillsense_test.catalog import Skill
        import hashlib
        root=Path(self.temp.name)
        skill=root/"SKILL.md"
        skill.write_text("Hermes native skills",encoding="utf-8")
        item=Skill("profile::existing","existing","Git repository maintenance",(),(),
                   str(skill),hashlib.sha256(skill.read_bytes()).hexdigest())
        conn=open_db()
        try:
            sync(conn,[item])
        finally:
            conn.close()
        with patch("skillsense_test.eligibility.native_skill_catalogue",
                   return_value={"existing":"Git repository maintenance"}):
            self.plugin._refresh_native()
        conn=open_db()
        try:
            self.assertEqual(len(rows(conn)),1)
        finally:
            conn.close()
