"""Routing should not repeat identical hints in the same session."""
import unittest
from test_catalog import module

class HintTests(unittest.TestCase):
    def setUp(self):
        module()

    def test_session_deduplication(self):
        import skillsense_test.routing as mod
        from unittest.mock import patch
        router=mod.Router([{"id":"a","name":"android-re","description":"APK reverse engineering",
            "tags":["android","apk"],"aliases":[],"intents":[]}])
        with patch.object(mod,"get_router",return_value=router):
            first=mod.hint("android-re APK","2",session_id="one")
            second=mod.hint("android-re APK",session_id="one")
            third=mod.hint("android-re APK",session_id="two")
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertIsNotNone(third)
        self.assertNotIn("IGNORE",first["context"])

    def test_cache_keys_never_hold_raw_session_identifiers(self):
        import skillsense_test.routing as mod
        from unittest.mock import patch
        router = mod.Router([{"id":"a","name":"android-re",
                             "description":"APK reverse engineering",
                             "tags":["android","apk"],"aliases":[],"intents":[]}])
        session = "very-private-session-reference"
        with mod._recent_lock:
            mod._recent.clear()
        with patch.object(mod, "get_router", return_value=router):
            self.assertIsNotNone(mod.hint("android-re APK", session_id=session))
            self.assertIsNone(mod.hint("android-re APK", session_id=session))
            # Invalid or unbounded IDs do not create unbounded session keys.
            self.assertIsNotNone(mod.hint("android-re APK", session_id="x"*100000))
            self.assertIsNotNone(mod.hint("android-re APK", session_id={"id":session}))
            with mod._recent_lock:
                self.assertEqual(len(mod._recent), 1)
                self.assertTrue(all(isinstance(key, bytes) and len(key) == 32
                                    for key in mod._recent))
                self.assertNotIn(session, mod._recent)
        with mod._recent_lock:
            mod._recent.clear()
