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
