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
