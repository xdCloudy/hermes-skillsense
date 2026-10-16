"""Import SkillSense as package from a standalone benchmark script."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys

def router_class():
    root=Path(__file__).resolve().parent.parent
    name="skillsense_bench"
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,root/"__init__.py",
                                                     submodule_search_locations=[str(root)])
        mod=importlib.util.module_from_spec(spec)
        sys.modules[name]=mod
        spec.loader.exec_module(mod)
    from skillsense_bench.routing import Router
    return Router
