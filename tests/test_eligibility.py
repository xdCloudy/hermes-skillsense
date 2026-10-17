"""Canonical Hermes list is the sole authority for routing availability."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from test_catalog import module

class EligibilityTests(unittest.TestCase):
    def setUp(self):
        module()

    def test_canonical_allowed_names_and_description(self):
        from skillsense_test.eligibility import filter_index_to_native
        records=[
            {"id":"profile:good","name":"android-re","source_description":"Inspect Android APK decompilation","description":"Enriched info"},
            {"id":"profile:disabled","name":"hidden","source_description":"Hidden skill"},
            {"id":"profile:ambiguous","name":"shadowed","source_description":"Outdated description"},
            {"id":"project:dup-a","name":"duplicate","source_description":"One"},
            {"id":"local:dup-b","name":"duplicate","source_description":"One"},
            {"id":"profile:missing","name":"no-description","source_description":""}
        ]
        allowed={"android-re":"Inspect Android APK decompilation",
                 "shadowed":"Different active description",
                 "duplicate":"One","no-description":"Fallback description"}
        result=filter_index_to_native(records,allowed)
        self.assertEqual([r["name"] for r in result],["android-re"])

    def test_native_catalog_failure_abstains(self):
        from skillsense_test.eligibility import native_skill_allowlist
        # Hermes is unavailable in ordinary unit-test environment.
        self.assertEqual(native_skill_allowlist(),{})

    def test_router_suppresses_stale_unavailable(self):
        from skillsense_test.routing import Router
        from skillsense_test.eligibility import filter_index_to_native
        records=[{"id":"1","name":"android-re","source_description":"Inspect APKs",
                  "description":"Inspect APKs","tags":["apk","android"],"aliases":[],
                  "intents":[]},
                 {"id":"2","name":"secret-disabled","source_description":"Do secret things",
                  "description":"Do secret things","tags":["secret"],"aliases":[],
                  "intents":[]}]
        router=Router(filter_index_to_native(records,{"android-re":"Inspect APKs"}))
        self.assertIsNone(router.suggest("secret-disabled"))
        self.assertIn("android-re",router.suggest("android-re APK"))

    def test_no_fail_open_when_catalog_missing(self):
        from skillsense_test.eligibility import filter_index_to_native
        self.assertEqual(filter_index_to_native([{"name":"anything"}],{}),[])

    def test_native_only_plugin_skill_is_searchable(self):
        from skillsense_test.eligibility import compose_native_records
        from skillsense_test.routing import Router
        names={"example:diagram":"Create SVG diagrams for architecture plans"}
        router=Router(compose_native_records([],names))
        self.assertIn("example:diagram",router.suggest("create SVG diagrams"))

    def test_shadowed_source_gets_native_description_not_stale_enrichment(self):
        from skillsense_test.eligibility import compose_native_records
        rows=[{"id":"stale","name":"android-re","description":"Never do work",
               "source_description":"Old skill description",
               "tags":["irrelevant"],"aliases":["wrong"],"intents":[]}]
        out=compose_native_records(rows,{"android-re":"Decompile Android APK archives"})
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]["description"],"Decompile Android APK archives")
        self.assertEqual(out[0]["tags"],[])
        self.assertEqual(out[0]["id"],"native::android-re")

    def test_canonical_catalogue_distinguishes_confirmed_empty_from_failure(self):
        import sys
        from types import ModuleType
        from skillsense_test.eligibility import native_skill_catalogue, native_skill_allowlist
        fake = ModuleType("tools.skills_tool")
        with patch.dict(sys.modules, {"tools.skills_tool": fake}):
            fake.skills_list = lambda: json.dumps({"success": True, "skills": []})
            self.assertEqual(native_skill_catalogue(), {})
            fake.skills_list = lambda: json.dumps({"success": False, "skills": []})
            self.assertIsNone(native_skill_catalogue())
            self.assertEqual(native_skill_allowlist(), {})
            fake.skills_list = lambda: "not JSON"
            self.assertIsNone(native_skill_catalogue())
            fake.skills_list = lambda: json.dumps({"success": True, "skills": [
                {"name":"visible","description":"Inspect local installed workflows"}]})
            self.assertEqual(native_skill_catalogue(),
                             {"visible":"Inspect local installed workflows"})
