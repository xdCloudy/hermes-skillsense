"""Exercise the local-only OpenAI-compatible transport with a real loopback stub."""
import json
import sys
import threading
import unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from test_catalog import module

class Stub(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_error(404);return
        size=int(self.headers.get("Content-Length","0"))
        body=json.loads(self.rfile.read(size))
        self.server.last_request=body
        answer={"choices":[{"message":{"content":json.dumps({
            "description":"APK reverse engineering", "tags":["apk","jadx"],
            "aliases":["decompile Android APK"],"positive_intents":[],
            "negative_intents":[]})}}]}
        data=json.dumps(answer).encode()
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def log_message(self,*args):
        pass

class LocalTransportTests(unittest.TestCase):
    def setUp(self):
        module()

    def test_complete_structured_local_round_trip(self):
        from skillsense_test.local_model import enrich
        server=ThreadingHTTPServer(("127.0.0.1",0),Stub)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            endpoint=f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
            result=enrich("SKILL.md text goes only to loopback", "my-model",endpoint)
            self.assertEqual(result["tags"],["apk","jadx"])
            self.assertEqual(server.last_request["model"],"my-model")
            self.assertIn("SKILL.md text",server.last_request["messages"][1]["content"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
