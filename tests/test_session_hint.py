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
