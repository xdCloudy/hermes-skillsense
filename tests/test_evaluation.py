"""Offline evaluator accepts user-provided labelled fixtures."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class EvaluationCLITests(unittest.TestCase):
    def test_custom_dataset(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            catalogue=root/"catalogue.json"
            cases=root/"cases.json"
            catalogue.write_text(json.dumps({"schema_version":1,"skills":[
                {"id":"a","name":"apk-review","description":"Inspect APK decompilation",
                 "tags":["apk","decompile"],"aliases":[],"intents":[]}]}))
            cases.write_text(json.dumps({"schema_version":1,"source":"independent-test",
                "cases":[{"id":"1","prompt":"review apk decompilation","gold":["apk-review"]},
                         {"id":"2","prompt":"hello there","gold":[]}]}))
            run=subprocess.run([sys.executable,str(ROOT/"tools"/"evaluate.py"),
                    "--json","--catalogue",str(catalogue),"--cases",str(cases)],
                    text=True,capture_output=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr)
            report=json.loads(run.stdout)
            self.assertEqual(report["dataset"],"independent-test")
            self.assertEqual(report["results"][2]["total"],2)

    def test_invalid_gold_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            catalogue=root/"catalogue.json"
            cases=root/"cases.json"
            catalogue.write_text(json.dumps({"schema_version":1,"skills":[]}))
            cases.write_text(json.dumps({"schema_version":1,"source":"test",
                "cases":[{"id":"bad","prompt":"test","gold":["nonexistent"]}]}))
            run=subprocess.run([sys.executable,str(ROOT/"tools"/"evaluate.py"),
                    "--catalogue",str(catalogue),"--cases",str(cases)],
                    text=True,capture_output=True,timeout=20)
            self.assertNotEqual(run.returncode,0)
            self.assertIn("unknown ground truth",run.stderr)

    def test_multilabel_micro_recall_differs_from_task_hit(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            cat=root/"catalogue.json"
            cases=root/"cases.json"
            cat.write_text(json.dumps({"schema_version":1,"skills":[
                {"id":"a","name":"apk-review","description":"APK decompilation",
                 "tags":["apk"],"aliases":[],"intents":[]},
                {"id":"b","name":"python-tests","description":"Python unit tests",
                 "tags":["python"],"aliases":[],"intents":[]}
            ]}),encoding="utf-8")
            cases.write_text(json.dumps({"schema_version":1,"source":"multi-label",
                "cases":[{"id":"multi","prompt":"apk-review decompilation",
                          "gold":["apk-review","python-tests"]}]}),encoding="utf-8")
            result=subprocess.run([sys.executable,str(ROOT/"tools"/"evaluate.py"),
                "--json","--catalogue",str(cat),"--cases",str(cases)],
                text=True,capture_output=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(result.stdout)["results"][2]
            self.assertEqual(report["top3_positive_hit_rate"],1.0)
            self.assertEqual(report["micro_recall_at_3"],0.5)
            self.assertEqual(report["counts"]["relevant_skill_labels"],2)
            self.assertIsNone(report["no_skill_false_positive_rate"])
            self.assertIsNone(report["wilson_95"]["no_skill_false_positive_rate"])

    def test_single_case_wilson_interval_is_not_false_certainty(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            cat=root/"catalogue.json"
            cases=root/"cases.json"
            cat.write_text(json.dumps({"schema_version":1,"skills":[
                {"id":"a","name":"apk-review","description":"APK decompilation",
                 "tags":["apk"],"aliases":[],"intents":[]}
            ]}),encoding="utf-8")
            cases.write_text(json.dumps({"schema_version":1,"source":"tiny",
                "cases":[{"id":"match","prompt":"apk-review decompilation","gold":["apk-review"]},
                         {"id":"none","prompt":"hello there","gold":[]}]}),
                encoding="utf-8")
            result=subprocess.run([sys.executable,str(ROOT/"tools"/"evaluate.py"),
                "--json","--catalogue",str(cat),"--cases",str(cases)],
                text=True,capture_output=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(result.stdout)["results"][2]
            low,high=report["wilson_95"]["positive_top1_hit_rate"]
            self.assertLess(low,0.25)
            self.assertEqual(high,1.0)
            fpr_low,fpr_high=report["wilson_95"]["no_skill_false_positive_rate"]
            self.assertEqual(fpr_low,0.0)
            self.assertGreater(fpr_high,0.75)

    def test_negative_intents_apply_only_to_enriched_variant(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            catalogue=root/"catalogue.json"
            cases=root/"cases.json"
            catalogue.write_text(json.dumps({
                "schema_version":1,
                "skills":[{
                    "id":"a","name":"apk-review",
                    "description":"Create Android APK apps",
                    "tags":["android","apk"],"aliases":[],"intents":[],
                    "negative_intents":["create an Android APK"]
                }]
            }),encoding="utf-8")
            cases.write_text(json.dumps({
                "schema_version":1,"source":"synthetic-regression",
                "cases":[{"id":"negative","prompt":"create an Android APK","gold":[]}]
            }),encoding="utf-8")
            run=subprocess.run([
                sys.executable,str(ROOT/"tools"/"evaluate.py"),"--json",
                "--catalogue",str(catalogue),"--cases",str(cases)
            ],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr)
            scores={item["variant"]:item["no_skill_false_positive_rate"]
                    for item in json.loads(run.stdout)["results"]}
            self.assertEqual(scores["source"],1.0)
            self.assertEqual(scores["enriched"],0.0)


    def test_reject_duplicate_catalogue_names_and_identifiers(self):
        base = {"schema_version": 1, "source": "validation regression",
                "cases": [{"id": "case-1", "prompt": "sample prompt", "gold": []}]}
        variants = [
            [{"id": "a", "name": "same"}, {"id": "b", "name": "same"}],
            [{"id": "a", "name": "first"}, {"id": "a", "name": "second"}],
        ]
        for skills in variants:
            with self.subTest(skills=skills), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                cat, cases = root / "catalogue.json", root / "cases.json"
                cat.write_text(json.dumps({"schema_version": 1, "skills": skills}),
                               encoding="utf-8")
                cases.write_text(json.dumps(base), encoding="utf-8")
                run = subprocess.run([sys.executable, str(ROOT / "tools" / "evaluate.py"),
                                      "--catalogue", str(cat), "--cases", str(cases)],
                                     text=True, capture_output=True, timeout=20)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn("duplicate skill name or ID", run.stderr)

    def test_reject_bad_metadata_and_duplicate_or_unhashable_labels(self):
        base_skill = {"id": "a", "name": "android-re", "description": "APK review"}
        cases = {"schema_version": 1, "source": "validation regression",
                 "cases": [{"id": "case-1", "prompt": "review apk", "gold": ["android-re"]}]}
        variants = [
            (dict(base_skill, tags="android"), cases, "invalid skill metadata"),
            (base_skill, dict(cases, cases=[dict(cases["cases"][0],
                                               gold=["android-re", "android-re"])]),
             "missing or unknown ground truth IDs"),
            (base_skill, dict(cases, cases=[dict(cases["cases"][0],
                                               gold=[["android-re"]])]),
             "missing or unknown ground truth IDs"),
        ]
        for skill, tasks, expected_error in variants:
            with self.subTest(expected_error=expected_error, skill=skill, tasks=tasks), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                cat, path = root / "catalogue.json", root / "cases.json"
                cat.write_text(json.dumps({"schema_version": 1, "skills": [skill]}),
                               encoding="utf-8")
                path.write_text(json.dumps(tasks), encoding="utf-8")
                run = subprocess.run([sys.executable, str(ROOT / "tools" / "evaluate.py"),
                                      "--catalogue", str(cat), "--cases", str(path)],
                                     text=True, capture_output=True, timeout=20)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn(expected_error, run.stderr)
