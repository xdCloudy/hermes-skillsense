"""Offline evaluation catalogue export must not touch prompt history or overwrite data."""
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from test_catalog import module

ROOT = Path(__file__).resolve().parents[1]


class ExportCatalogueTests(unittest.TestCase):
    def setUp(self):
        module()

    def run_cli(self, root, output):
        return subprocess.run(
            [sys.executable, str(ROOT / "tools" / "export_catalogue.py"),
             "--data-dir", str(root), "--output", str(output)],
            capture_output=True, text=True, timeout=20
        )

    def test_snapshot_only_export_for_plugin_skill(self):
        from skillsense_test.store import save_native_snapshot
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp) / "data"
            save_native_snapshot({"diagram:draw": "Draw architecture diagrams"}, data)
            output = Path(temp) / "catalogue.json"
            result = self.run_cli(data, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            parsed = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(parsed["schema_version"], 1)
            self.assertEqual(len(parsed["skills"]), 1)
            self.assertEqual(parsed["skills"][0]["name"], "diagram:draw")
            self.assertEqual(parsed["skills"][0]["description"], "Draw architecture diagrams")
            self.assertEqual(parsed["skills"][0]["negative_intents"], [])
            self.assertNotIn("cases", parsed)

    def test_never_overwrites_existing_output(self):
        from skillsense_test.store import save_native_snapshot
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp) / "data"
            save_native_snapshot({"a": "A skill"}, data)
            output = Path(temp) / "existing.json"
            output.write_text("private dataset", encoding="utf-8")
            result = self.run_cli(data, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "private dataset")

    def test_missing_or_expired_native_snapshot_is_rejected(self):
        from skillsense_test.store import save_native_snapshot
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp) / "data"
            data.mkdir()
            target = Path(temp) / "catalogue.json"
            self.assertNotEqual(self.run_cli(data, target).returncode, 0)
            self.assertFalse(target.exists())
            save_native_snapshot({"a": "A skill"}, data)
            snap = data / "native-catalogue.json"
            doc = json.loads(snap.read_text(encoding="utf-8"))
            doc["captured_at"] = 0
            snap.write_text(json.dumps(doc), encoding="utf-8")
            self.assertNotEqual(self.run_cli(data, target).returncode, 0)
            self.assertFalse(target.exists())

    def test_export_preserves_approved_negative_intents(self):
        from skillsense_test.store import save_native_snapshot
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            data=root/"data"
            save_native_snapshot({"android-re":"Inspect APK code"},data)
            (data/"index.json").write_text(json.dumps({
                "schema":1, "skills":[{
                    "id":str(root/"private-profile") + "::android-re","name":"android-re",
                    "source_description":"Inspect APK code",
                    "description":"Inspect and decompile APK code",
                    "tags":["apk","jadx"],"aliases":["decompile apk"],
                    "intents":["inspect android bytecode"],
                    "negative_intents":["create an android apk"]
                }]
            }),encoding="utf-8")
            output=root/"catalogue.json"
            result=self.run_cli(data,output)
            self.assertEqual(result.returncode,0,result.stderr)
            exported=json.loads(output.read_text(encoding="utf-8"))["skills"][0]
            self.assertEqual(exported["aliases"],["decompile apk"])
            self.assertEqual(exported["negative_intents"],["create an android apk"])
            self.assertEqual(exported["id"], "export::00001")
            self.assertNotIn(str(root), output.read_text(encoding="utf-8"))

    @unittest.skipUnless(os.name == "posix", "POSIX permissions only")
    def test_output_is_private_even_with_permissive_umask(self):
        from skillsense_test.store import save_native_snapshot
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data"
            save_native_snapshot({"private-skill": "Private metadata"}, data)
            target = root / "nested" / "catalogue.json"
            old_umask = os.umask(0)
            try:
                result = self.run_cli(data, target)
            finally:
                os.umask(old_umask)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(target.parent.stat().st_mode), 0o700)
            self.assertIn("private-skill", target.read_text(encoding="utf-8"))

    def test_symlink_target_is_never_followed_or_overwritten(self):
        from skillsense_test.store import save_native_snapshot
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data"
            save_native_snapshot({"skill": "Private skill description"}, data)
            existing = root / "existing.json"
            existing.write_text("protected original", encoding="utf-8")
            symlink = root / "catalogue.json"
            try:
                symlink.symlink_to(existing)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            result = self.run_cli(data, symlink)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(existing.read_text(encoding="utf-8"), "protected original")
