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
