"""Standard-library regression tests for the standalone search core."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import BM25Index, Document, tokenize  # noqa: E402


class TokenizeTests(unittest.TestCase):
    def test_case_punctuation(self):
        self.assertEqual(tokenize("APK_decompile, Java"), ("apk", "decompile", "java"))

    def test_unicode(self):
        self.assertEqual(tokenize("CAFÉ"), ("café",))


class BM25Tests(unittest.TestCase):
    def setUp(self):
        self.index = BM25Index(
            [
                Document("android-re", "Android APK decompile JADX DEX"),
                Document("web-design", "CSS web design layout"),
                Document("java", "Java compile code classes"),
            ]
        )

    def test_retrieves_most_relevant_document(self):
        self.assertEqual(self.index.search("decompile this apk")[0].skill_id, "android-re")

    def test_empty_query_and_no_match(self):
        self.assertEqual(self.index.search(""), [])
        self.assertEqual(self.index.search("unmentioned"), [])

    def test_limit(self):
        self.assertEqual(self.index.search("apk", limit=0), [])
        self.assertLessEqual(len(self.index.search("apk", limit=1)), 1)

    def test_duplicate_ids_fail(self):
        with self.assertRaises(ValueError):
            BM25Index([Document("a", "one"), Document("a", "two")])

    def test_invalid_parameters_fail(self):
        with self.assertRaises(ValueError):
            BM25Index([], k1=float("nan"))
        with self.assertRaises(ValueError):
            BM25Index([], b=-1)

    def test_deterministic_tie(self):
        index = BM25Index([Document("z", "apple"), Document("a", "apple")])
        self.assertEqual([m.skill_id for m in index.search("apple")], ["a", "z"])

    def test_empty_index(self):
        self.assertEqual(BM25Index([]).search("whatever"), [])


if __name__ == "__main__":
    unittest.main()
