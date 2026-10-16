"""Registration contract tests using a mock Hermes plugin context."""

import importlib.util
from pathlib import Path
import unittest


PLUGIN_PATH = Path(__file__).resolve().parents[1] / "__init__.py"


def load_plugin():
    spec = importlib.util.spec_from_file_location("skillsense_under_test", PLUGIN_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StubContext:
    def __init__(self):
        self.hooks = {}
        self.cli = {}
        self.commands = {}

    def register_hook(self, name, fn):
        self.hooks[name] = fn

    def register_cli_command(self, **kwargs):
        self.cli[kwargs["name"]] = kwargs

    def register_command(self, name, **kwargs):
        self.commands[name] = kwargs


class PluginTests(unittest.TestCase):
    def test_registration_and_no_op_inference(self):
        plugin = load_plugin()
        ctx = StubContext()
        plugin.register(ctx)
        self.assertIn("pre_llm_call", ctx.hooks)
        self.assertIn("skillrouter", ctx.cli)
        self.assertIn("skillrouter", ctx.commands)
        self.assertIsNone(ctx.hooks["pre_llm_call"](user_message="test", session_id="x"))
        self.assertIn("not implemented", ctx.commands["skillrouter"]["handler"]("status"))


if __name__ == "__main__":
    unittest.main()
