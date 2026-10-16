"""Simple cross-platform zero-dependency repository structure checker."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "README.md", "SPEC.md", "GOAL.md", "ARCHITECTURE.md", "ROADMAP.md",
    "AGENTS.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE",
    "CODE_OF_CONDUCT.md", "CHANGELOG.md", "SUPPORT.md", "MAINTAINERS.md",
    "plugin.yaml", "__init__.py", "core.py", "catalog.py", "store.py",
    "routing.py", "eligibility.py", "local_model.py", "assets/skillsense-logo.png",
    "docs/DEVELOPMENT.md", "docs/CONFIGURATION.md", "docs/BENCHMARKS.md",
    "docs/INTEGRATION.md", "docs/METADATA_SCHEMA.md", "docs/EVALUATION.md",
    "tools/evaluate.py", "tools/routing_import.py",
    "benchmarks/selection-cases-v1.json", "benchmarks/selection-catalogue-v1.json",
    "tests/test_core.py", "tests/test_plugin.py", "tests/test_eligibility.py",
    "tests/test_clean_integration.py", "tests/test_evaluation.py",
]
missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
if missing:
    print("Missing project files:", ", ".join(missing), file=sys.stderr)
    sys.exit(1)

image = (ROOT / "assets/skillsense-logo.png").read_bytes()
if not image.startswith(b"\x89PNG\r\n\x1a\n"):
    print("Logo is not a PNG", file=sys.stderr)
    sys.exit(1)

print(f"SkillSense structure OK: {len(REQUIRED)} required files")
