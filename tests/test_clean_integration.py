"""End-to-end Metadata Clean against a real loopback model stub, no cloud."""
import argparse
import hashlib
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from test_plugin import load_plugin

class ModelStub(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length))
        self.server.requests.append(request)
        generated = {"description": "Inspect and decompile Android APK code",
                     "tags":["android","apk","jadx"],
                     "aliases":["decompile APK"],"positive_intents":["inspect Android bytecode"],
                     "negative_intents":["create a new website"]}
        response = {"choices":[{"message":{"content":json.dumps(generated)}}]}
        data = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self,*args):
        pass

class MetadataCleanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_home = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = self.temp.name
        self.root = Path(self.temp.name)/"skills"
        self.skill_dir = self.root/"android-re"
        self.skill_dir.mkdir(parents=True)
        self.source = self.skill_dir/"SKILL.md"
        self.source.write_text(
            "---\nname: android-re\ndescription: Inspect Android APK code\n---\n"
            "## When to Use\nDecompile APK files for diagnostics.\n",encoding="utf-8"
        )
        self.plugin = load_plugin()
        self.server = ThreadingHTTPServer(("127.0.0.1",0),ModelStub)
        self.server.requests = []
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=4)
        if self.original_home is None:
            os.environ.pop("HERMES_HOME",None)
        else:
            os.environ["HERMES_HOME"] = self.original_home
        self.temp.cleanup()

    def test_local_model_stages_pending_and_requires_approval(self):
        from skillsense_test.store import open_db, rows, read_index
        original = self.source.read_bytes()
        url = f"http://127.0.0.1:{self.server.server_port}/v1/chat/completions"
        result = self.plugin._clean(argparse.Namespace(
            roots=[str(self.root)],model="aux",dry_run=False,force=False,
            endpoint=url,model_id="local-only"
        ))
        self.assertIn("1 pending review",result)
        self.assertEqual(len(self.server.requests),1)
        self.assertIn("Decompile APK",self.server.requests[0]["messages"][1]["content"])
        self.assertEqual(self.source.read_bytes(),original)
        conn = open_db()
        try:
            row=rows(conn)[0]
            self.assertEqual(row["status"],"pending")
            self.assertIsNone(row["approved"])
            self.assertIn("jadx",row["pending"]["tags"])
        finally:
            conn.close()
        approval=self.plugin._review(argparse.Namespace(review_action="approve",skill="android-re"))
        self.assertIn("Approved",approval)
        self.assertIn("jadx",read_index()[0]["tags"])
        self.assertEqual(self.source.read_bytes(),original)

    def test_rebuild_and_dry_run_make_no_model_calls(self):
        self.plugin._rebuild(argparse.Namespace(roots=[str(self.root)]))
        result=self.plugin._clean(argparse.Namespace(
            roots=[str(self.root)],model="none",dry_run=True,
            force=False,endpoint=None,model_id=None))
        self.assertIn("no files or database changed",result)
        self.assertEqual(self.server.requests,[])
