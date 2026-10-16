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

    def test_multimodal_and_nontext_user_turns_abstain(self):
        from skillsense_test.routing import Router
        router = Router([{"id":"a","name":"android-re",
                          "description":"Decompile Android APK",
                          "tags":["apk"],"aliases":[],"intents":[]}])
        for message in (
            [{"type":"text","text":"android-re decompile APK"},
             {"type":"image_url","image_url":{"url":"data:image/png;base64,SECRET"}}],
            {"text":"android-re decompile APK"},
            b"android-re decompile APK", 123, None,
        ):
            with self.subTest(message_type=type(message).__name__):
                self.assertIsNone(router.suggest(message))
        self.assertIn("android-re",router.suggest("android-re decompile APK"))

    def test_long_user_text_does_not_require_unbounded_normalization(self):
        from unittest.mock import patch
        import skillsense_test.routing as routing
        router = routing.Router([{"id":"a","name":"android-re",
                                 "description":"Decompile Android APK",
                                 "tags":["apk"],"aliases":[],"intents":[]}])
        original = routing.clean_text
        lengths = []
        def bounded(value, max_len=240):
            lengths.append(len(value))
            return original(value, max_len)
        with patch.object(routing,"clean_text",side_effect=bounded):
            result = router.suggest("android-re decompile APK " + "a"*250000)
        self.assertIn("android-re",result)
        self.assertLessEqual(max(lengths),2000)

    def test_ambiguous_secondary_skill_never_leaks_into_hint(self):
        from skillsense_test.routing import Router
        router = Router([
            {"id":"main","name":"apk-review",
             "description":"apk review verify android app",
             "tags":["apk","review"],"aliases":[],"intents":[]},
            {"id":"first","name":"apk-tools",
             "description":"apk review verify android app",
             "tags":["apk"],"aliases":[],"intents":[]},
            {"id":"second","name":"apk-tools",
             "description":"apk review verify android app",
             "tags":["apk"],"aliases":[],"intents":[]},
        ])
        from unittest.mock import patch
        from skillsense_test.core import Match
        # Test secondary candidate eligibility independently of BM25 weights.
        # The top candidate is unambiguous, while both trailing IDs share a name.
        candidates = [Match("main",10.0),Match("first",9.0),Match("second",8.0)]
        with patch.object(router.index,"search",return_value=candidates):
            hint = router.suggest("apk-review apk tools verify android app",3)
        self.assertIsNotNone(hint)
        self.assertIn("- apk-review",hint)
        self.assertNotIn("- apk-tools",hint)
