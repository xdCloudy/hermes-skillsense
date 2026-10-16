import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_catalog import module
class SafetyTests(unittest.TestCase):
    def setUp(self):
        module()
    def test_endpoint_must_be_explicit_numeric_loopback(self):
        from skillsense_test.local_model import endpoint,LocalOnlyError
        for url in ("https://127.0.0.1:8000/v1/chat/completions",
                    "http://example.com/v1/chat/completions",
                    "http://localhost:8000/v1/chat/completions",
                    "http://192.168.1.1:8000/v1/chat/completions",
                    "http://127.0.0.1:8000/other",
                    "http://127.0.0.1:8000/v1/chat/completions?x=y",
                    "http://u:p@127.0.0.1:8000/v1/chat/completions"):
            with self.assertRaises(LocalOnlyError,msg=url):
                endpoint(url)
        self.assertEqual(endpoint("http://127.0.0.1:8000/v1/chat/completions"),
                         "http://127.0.0.1:8000/v1/chat/completions")
        self.assertEqual(endpoint("http://[::1]:8011/v1/chat/completions"),
                         "http://[::1]:8011/v1/chat/completions")

    def test_refuses_unsafe_destination_without_network(self):
        from skillsense_test.local_model import enrich,LocalOnlyError
        with self.assertRaises(LocalOnlyError):
            enrich("private file", "local-model",
                   "https://api.example.com/v1/chat/completions")
