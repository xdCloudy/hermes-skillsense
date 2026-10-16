"""Regression tests for missing and incomplete SKILL.md metadata."""
from pathlib import Path
import tempfile
import unittest
from test_catalog import module

class IncompleteMetadataTests(unittest.TestCase):
    def setUp(self):
        module()

    def test_no_frontmatter_is_indexed_by_directory_name(self):
        from skillsense_test.catalog import scan_skills
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"plain-skill"
            path.mkdir()
            (path/"SKILL.md").write_text("# Plain Skill\n## When to Use\nDo a plain task.\n")
            result=scan_skills([Path(temp)])
            self.assertEqual(len(result),1)
            self.assertEqual(result[0].name,"plain-skill")
            self.assertEqual(result[0].tags,())

    def test_malformed_frontmatter_falls_back(self):
        from skillsense_test.catalog import scan_skills
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"fallback"
            path.mkdir()
            (path/"SKILL.md").write_text("---\ninvalid: [yaml\n# Missing terminator")
            result=scan_skills([Path(temp)])
            self.assertEqual(len(result),1)
            self.assertEqual(result[0].name,"fallback")

    def test_symlinked_skill_file_excluded(self):
        from skillsense_test.catalog import scan_skills
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            outside=root/"private.md"
            outside.write_text("private")
            skill=root/"linked"
            skill.mkdir()
            try:
                (skill/"SKILL.md").symlink_to(outside)
            except (OSError,NotImplementedError):
                self.skipTest("symlinks unavailable")
            self.assertEqual(scan_skills([root]),[])
