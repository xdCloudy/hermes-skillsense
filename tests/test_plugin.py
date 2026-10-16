"""Integration surface test using mock Hermes PluginContext."""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class StubContext:
    def __init__(self):
        self.hooks={};self.cli={};self.commands={};self.tasks={};self.settings={}
    def register_hook(self,name,fn): self.hooks[name]=fn
    def register_cli_command(self,**kwargs): self.cli[kwargs["name"]]=kwargs
    def register_command(self,name,**kwargs): self.commands[name]=kwargs
    def register_auxiliary_task(self,name,**kwargs): self.tasks[name]=kwargs
    def get_config(self,key,default=None): return self.settings.get(key,default)
    def set_config(self,key,value): self.settings[key]=value

def load_plugin():
    spec=importlib.util.spec_from_file_location("skillsense_test",ROOT/"__init__.py",
                                                submodule_search_locations=[str(ROOT)])
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod; spec.loader.exec_module(mod)
    return mod

class PluginTests(unittest.TestCase):
    def test_registration_does_not_inject_before_enable(self):
        with tempfile.TemporaryDirectory() as temp:
            prior=os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"]=temp
            try:
                mod=load_plugin();ctx=StubContext();mod.register(ctx)
                self.assertIn("pre_llm_call",ctx.hooks)
                self.assertIn("skillrouter",ctx.cli)
                self.assertIn("skillrouter",ctx.commands)
                self.assertIn("skillrouter_tagger",ctx.tasks)
                self.assertIsNone(ctx.hooks["pre_llm_call"](user_message="decompile apk"))
                self.assertIn("SkillSense",ctx.commands["skillrouter"]["handler"]("status"))
            finally:
                if prior is None: os.environ.pop("HERMES_HOME",None)
                else: os.environ["HERMES_HOME"]=prior

    def test_bad_settings_fail_closed_without_breaking_registration(self):
        with tempfile.TemporaryDirectory() as temp:
            prior=os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"]=temp
            try:
                plugin=load_plugin()
                ctx=StubContext()
                ctx.settings={"enabled":"false","max_suggestions":"not a number"}
                plugin.register(ctx)
                self.assertIn("pre_llm_call",ctx.hooks)
                self.assertIsNone(ctx.hooks["pre_llm_call"](user_message="android-re APK"))
                self.assertIn("skillrouter",ctx.cli)
            finally:
                if prior is None: os.environ.pop("HERMES_HOME",None)
                else: os.environ["HERMES_HOME"]=prior
