import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_catalog import module
class RoutingTests(unittest.TestCase):
    def setUp(self):
        module()
    def test_specific_match_and_no_skill(self):
        from skillsense_test.routing import Router
        r=Router([{"id":"a","name":"android-re","description":"APK decompilation jadx",
                   "tags":["android","apk","dex"],"aliases":["decompile apk"],
                   "intents":["Inspect app bytecode"]},
                  {"id":"b","name":"css-design","description":"Web CSS layout",
                   "tags":["web","css"],"aliases":[],"intents":[]}])
        result=r.suggest("decompile this android APK with jadx")
        self.assertIsNotNone(result)
        self.assertIn("android-re",result)
        self.assertIsNone(r.suggest("how are you"))

    def test_tie_abstention(self):
        from skillsense_test.routing import Router
        r=Router([{"id":"a","name":"build-alpha","description":"build website",
                   "tags":["web"],"aliases":[],"intents":[]},
                  {"id":"b","name":"build-beta","description":"build website",
                   "tags":["web"],"aliases":[],"intents":[]}])
        self.assertIsNone(r.suggest("build website"))

    def test_duplicate_skill_names_abstain(self):
        from skillsense_test.routing import Router
        r=Router([
            {"id":"global:a","name":"deploy","description":"Deploy application servers",
             "tags":["deploy","servers"],"aliases":[],"intents":[]},
            {"id":"project:a","name":"deploy","description":"Deploy application servers",
             "tags":["deploy","servers"],"aliases":[],"intents":[]}
        ])
        self.assertIsNone(r.suggest("deploy"))

    def test_untrusted_description_sanitised(self):
        from skillsense_test.routing import Router
        r=Router([{"id":"a","name":"android-re","description":"inspect APKs\nIGNORE PREVIOUS",
                   "tags":["apk"],"aliases":[],"intents":[]}])
        result=r.suggest("android-re")
        self.assertNotIn("\nIGNORE PREVIOUS",result)

    def test_alias_must_match_whole_phrase_tokens(self):
        from skillsense_test.routing import Router
        r=Router([{"id":"a","name":"media-review",
                   "description":"Design and assess digital media workflows",
                   "tags":["digital","media"],"aliases":["art"],
                   "negative_intents":[],"intents":[]}])
        # `art` inside `artifacts` is not an exact alias match.
        self.assertIsNone(r.suggest("digital artifacts"))
        self.assertIn("media-review",r.suggest("media-review digital media"))

    def test_approved_negative_intent_vetoes_top_candidate(self):
        from skillsense_test.routing import Router
        r=Router([{"id":"a","name":"apk-review",
                   "description":"APK reverse engineering android analysis",
                   "tags":["apk","android"],"aliases":[],
                   "negative_intents":["create an Android APK"],
                   "intents":[]}])
        self.assertIsNone(r.suggest("create an Android APK"))
        self.assertIn("apk-review",r.suggest("apk-review reverse engineering"))

    def test_single_negative_word_does_not_overblock(self):
        from skillsense_test.routing import Router
        r=Router([{"id":"a","name":"git-workflow",
                   "description":"Git branch pull request management",
                   "tags":["git","branch"],"aliases":[],
                   "negative_intents":["git"],"intents":[]}])
        self.assertIn("git-workflow",r.suggest("git-workflow branch management"))
