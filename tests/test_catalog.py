import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
def module():
    spec = importlib.util.spec_from_file_location("skillsense_test",ROOT/"__init__.py",
                                                  submodule_search_locations=[str(ROOT)])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod

class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.pkg=module()

    def test_scans_and_extracts_without_writing(self):
        from skillsense_test.catalog import scan_skills
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); skill=root/"android-re"; skill.mkdir()
            source=skill/"SKILL.md"
            content='---\nname: android-re\ndescription: Inspect Android APKs\nmetadata:\n  hermes:\n    tags: [android, jadx, apk]\n---\n## When to Use\nInvestigate APK files.\n## Procedure\nDo stuff.'
            source.write_text(content)
            before=source.read_bytes()
            result=scan_skills([root])
            self.assertEqual(len(result),1)
            self.assertEqual(result[0].name,"android-re")
            self.assertIn("jadx",result[0].tags)
            self.assertIn("Investigate",result[0].intents[0])
            self.assertEqual(source.read_bytes(),before)

    def test_invalid_restrictions_excluded(self):
        from skillsense_test.catalog import scan_skills
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/"danger").mkdir()
            (root/"danger"/"SKILL.md").write_text("---\nname: danger\nplatforms: [linux]\n---\n")
            self.assertEqual(scan_skills([root]),[])

    def test_rejects_bad_model_metadata(self):
        from skillsense_test.catalog import validate_proposal
        for value in ({"aliases":"oops"},{"shell":"sudo rm -rf /"},{"tags":["x"]*20},
                      {"description":""}):
            with self.assertRaises(ValueError):
                validate_proposal(value)
        good=validate_proposal({"description":"Inspect APKs","tags":["Android","android"],
                                "positive_intents":["decompile an APK"]})
        self.assertEqual(len(good["tags"]),1)

    def test_symlinked_trusted_root_is_supported(self):
        from skillsense_test.catalog import scan_skills
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"one";root.mkdir()
            (root/"sample").mkdir()
            (root/"sample"/"SKILL.md").write_text("# Sample skill\n## When to Use\nReview code.")
            link=Path(temp)/"link"
            try:
                link.symlink_to(root,target_is_directory=True)
            except (OSError,NotImplementedError):
                self.skipTest("symlink creation unsupported")
            self.assertEqual(len(scan_skills([link])),1)  # explicit trusted root resolves

    def test_missing_frontmatter_description_uses_native_body_fallback(self):
        from skillsense_test.catalog import scan_skills
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);directory=root/"markdown-only";directory.mkdir()
            (directory/"SKILL.md").write_text(
                "# Markdown skill\n\nFirst non-heading line describing data analysis.\n"
                "## When to Use\nAnalyse some data.",encoding="utf-8")
            found=scan_skills([root])
            self.assertEqual(found[0].description,
                             "First non-heading line describing data analysis.")

    def test_truncated_root_scan_fails_before_sync(self):
        from unittest.mock import patch
        from skillsense_test.catalog import scan_skills
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for n in ("one","two"):
                folder=root/n
                folder.mkdir()
                (folder/"SKILL.md").write_text(
                    "---\\nname: "+n+"\\ndescription: Test skill\\n---\\n")
            with patch("skillsense_test.catalog.MAX_SKILLS",1):
                with self.assertRaisesRegex(ValueError,"maximum"):
                    scan_skills([root])
