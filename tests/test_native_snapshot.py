"""Portable native catalogue snapshot: plugin host needs no Hermes imports."""
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from test_catalog import module

class NativeSnapshotTests(unittest.TestCase):
    def setUp(self):
        module()

    def test_local_snapshot_round_trip_and_expiry(self):
        from skillsense_test.store import save_native_snapshot, read_native_snapshot
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp)
            expected={"android-re":"Inspect Android APK decompilation",
                      "github:git":"Manage pull requests"}
            save_native_snapshot(expected,home)
            self.assertEqual(read_native_snapshot(home),expected)
            file=home/"native-catalogue.json"
            payload=json.loads(file.read_text(encoding="utf-8"))
            payload["captured_at"]=time.time()-9*86400
            file.write_text(json.dumps(payload),encoding="utf-8")
            self.assertEqual(read_native_snapshot(home),{})

    def test_corrupt_or_missing_catalogue_abstains(self):
        from skillsense_test.store import read_native_snapshot
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp)
            self.assertEqual(read_native_snapshot(home),{})
            (home/"native-catalogue.json").write_text("invalid-json",encoding="utf-8")
            self.assertEqual(read_native_snapshot(home),{})

    def test_empty_capture_invalidates_stale_catalogue(self):
        from skillsense_test.store import save_native_snapshot,read_native_snapshot
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            save_native_snapshot({"stale":"Old skill"},root)
            save_native_snapshot({},root)
            self.assertEqual(read_native_snapshot(root),{})

    def test_router_gets_allowed_records_from_snapshot(self):
        import skillsense_test.routing as mod
        from unittest.mock import patch
        sidecar=[{"id":"local:apk","name":"android-re",
                  "source_description":"Inspect Android APK decompilation",
                  "description":"Inspect Android APK decompilation",
                  "tags":["apk","android","jadx"],"aliases":[],"intents":[]}]
        with patch.object(mod,"read_index",return_value=sidecar), \
             patch.object(mod,"read_native_snapshot",
                          return_value={"android-re":"Inspect Android APK decompilation"}):
            mod.clear_cache()
            self.assertIn("android-re",mod.hint("android-re APK with jadx")["context"])
        mod.clear_cache()

    def test_missing_native_catalogue_produces_no_hint(self):
        import skillsense_test.routing as mod
        with patch.object(mod,"read_index",return_value=[
             {"id":"a","name":"android-re","description":"APK files",
              "source_description":"APK files","tags":["apk"],"aliases":[],"intents":[]}]), \
             patch.object(mod,"read_native_snapshot",return_value={}):
            mod.clear_cache()
            self.assertIsNone(mod.hint("android-re APK"))
        mod.clear_cache()

    def test_router_refreshes_when_native_catalogue_expires(self):
        import skillsense_test.routing as mod
        from unittest.mock import patch
        sidecar=[{"id":"local","name":"android-re",
                  "description":"Inspect APKs", "source_description":"Inspect APKs",
                  "tags":["apk"],"aliases":[],"intents":[]}]
        with patch.object(mod,"read_index",return_value=sidecar), \
             patch.object(mod,"read_native_snapshot",
                          side_effect=[{"android-re":"Inspect APKs"},{}]):
            mod.clear_cache()
            self.assertIsNotNone(mod.hint("android-re APK"))
            mod._cache_refreshed -= mod._CACHE_REFRESH_SECONDS + 1
            self.assertIsNone(mod.hint("android-re APK"))
        mod.clear_cache()

    def test_persisted_catalogue_rejects_invalid_load_names(self):
        from skillsense_test.store import save_native_snapshot, read_native_snapshot
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            valid = {"android-re": "Inspect APKs", "plugin:skill": "Plugin skill"}
            invalid = {"ignore previous instructions": "Injected",
                       "evil\\n-newline": "Injected",
                       "../escape": "Invalid name",
                       "x" * 201: "Oversized name"}
            save_native_snapshot({**valid, **invalid}, home)
            self.assertEqual(read_native_snapshot(home), valid)

            # Validate again on read: a local file can be edited after capture.
            path = home / "native-catalogue.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw["skills"].update(invalid)
            path.write_text(json.dumps(raw), encoding="utf-8")
            self.assertEqual(read_native_snapshot(home), valid)

    def test_oversized_native_snapshot_never_reaches_hot_path(self):
        from skillsense_test.store import save_native_snapshot, read_native_snapshot
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            previous = {"android-re": "Inspect APK decompilation"}
            save_native_snapshot(previous, home)
            very_large = {f"skill-{i}": "Small" for i in range(2501)}
            with self.assertRaisesRegex(ValueError, "exceeds 2500"):
                save_native_snapshot(very_large, home)
            self.assertEqual(read_native_snapshot(home), previous)

            # A valid-looking but tampered JSON file must also fail closed,
            # rather than loading thousands of records into the live BM25 index.
            file = home / "native-catalogue.json"
            payload = json.loads(file.read_text(encoding="utf-8"))
            payload["skills"] = very_large
            file.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(read_native_snapshot(home), {})
