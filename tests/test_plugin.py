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

    def test_doctor_is_read_only_without_catalogue(self):
        with tempfile.TemporaryDirectory() as temp:
            previous=os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"]=temp
            try:
                plugin=load_plugin()
                message=plugin._diagnostics()
                self.assertIn("index missing",message)
                self.assertFalse((Path(temp)/"plugin-data"/"skillsense"/"data.db").exists())
            finally:
                if previous is None: os.environ.pop("HERMES_HOME",None)
                else: os.environ["HERMES_HOME"]=previous

    def test_doctor_catches_stale_native_catalogue(self):
        with tempfile.TemporaryDirectory() as temp:
            previous=os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"]=temp
            try:
                plugin=load_plugin()
                from skillsense_test.store import save_native_snapshot, open_db, publish_index
                conn=open_db()
                try:
                    publish_index(conn)
                finally:
                    conn.close()
                self.assertIn("native skill catalogue missing",plugin._diagnostics())
                save_native_snapshot({})
                self.assertIn("routing will abstain",plugin._diagnostics())
            finally:
                if previous is None: os.environ.pop("HERMES_HOME",None)
                else: os.environ["HERMES_HOME"]=previous

    def test_enable_requires_index_even_with_native_settings(self):
        import argparse
        with tempfile.TemporaryDirectory() as temp:
            previous=os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"]=temp
            try:
                plugin=load_plugin()
                ctx=StubContext()
                with self.assertRaisesRegex(ValueError,"rebuild"):
                    plugin._configure(argparse.Namespace(action="enable"),ctx)
                self.assertNotIn("enabled",ctx.settings)
            finally:
                if previous is None: os.environ.pop("HERMES_HOME",None)
                else: os.environ["HERMES_HOME"]=previous

    def test_enable_requires_live_native_snapshot_and_accepts_valid_one(self):
        import argparse
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            prior=os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"]=temp
            try:
                plugin=load_plugin()
                from skillsense_test.store import save_native_snapshot, open_db, publish_index
                conn=open_db()
                try:
                    publish_index(conn)
                finally:
                    conn.close()
                ctx=StubContext()
                with self.assertRaisesRegex(ValueError,"availability missing"):
                    plugin._configure(argparse.Namespace(action="enable"),ctx)
                self.assertNotIn("enabled",ctx.settings)
                save_native_snapshot({"native-skill":"Installed native skill"})
                self.assertIn("enabled",plugin._configure(
                    argparse.Namespace(action="enable"),ctx))
                self.assertIs(ctx.settings["enabled"],True)
                self.assertIn("disabled",plugin._configure(
                    argparse.Namespace(action="disable"),ctx))
                self.assertIs(ctx.settings["enabled"],False)
            finally:
                if prior is None: os.environ.pop("HERMES_HOME",None)
                else: os.environ["HERMES_HOME"]=prior

    def test_status_reports_native_only_catalogue_and_stale_inactivity(self):
        with tempfile.TemporaryDirectory() as temp:
            previous=os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"]=temp
            try:
                plugin=load_plugin()
                from skillsense_test.store import open_db, publish_index, save_native_snapshot
                db=open_db()
                try:
                    publish_index(db)
                finally:
                    db.close()
                save_native_snapshot({"plugin:svg":"Draw SVG diagrams"})
                active=plugin._status(enabled_setting=True)
                self.assertIn("0 skills in sidecar",active)
                self.assertIn("1 native-available",active)
                self.assertIn("routing enabled",active)
                save_native_snapshot({})
                stale=plugin._status(enabled_setting=True)
                self.assertIn("0 native-available",stale)
                self.assertIn("configured but inactive",stale)
                self.assertIn("routing disabled",plugin._status(enabled_setting=False))
            finally:
                if previous is None: os.environ.pop("HERMES_HOME",None)
                else: os.environ["HERMES_HOME"]=previous

    def test_doctor_reports_corrupt_index_not_misleading_healthy_state(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            prior = os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"] = temp
            try:
                plugin = load_plugin()
                from skillsense_test.store import (open_db, publish_index,
                                                  save_native_snapshot, data_dir)
                conn = open_db()
                try:
                    publish_index(conn)
                finally:
                    conn.close()
                save_native_snapshot({"android-re":"Inspect Android APKs"})
                self.assertIn("eligible candidates", plugin._diagnostics())

                (data_dir()/"index.json").write_text(
                    json.dumps({"schema": 1, "skills": [
                        {"id":"injected","name":"android-re","aliases":"bad"}
                    ]}), encoding="utf-8")
                result = plugin._diagnostics()
                self.assertIn("index invalid", result)
                self.assertIn("native-only", result)
                self.assertIn("rebuild", result)
            finally:
                if prior is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = prior
