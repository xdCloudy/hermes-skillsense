"""Never send commonly recognised private credentials to local audit models."""
import unittest
from test_catalog import module

class RedactionTests(unittest.TestCase):
    def setUp(self):
        module()

    def test_private_key_and_bearer_are_redacted(self):
        from skillsense_test.local_model import redact_skill_text
        source=(
            "# Skill description\n"
            "-----BEGIN PRIVATE KEY-----\n"
            "PRIVATE-MATERIAL-IN-TEST\n"
            "-----END PRIVATE KEY-----\n"
            "curl -H 'Authorization: Bearer verysecretbearertoken12345'\n"
            "description: GitHub PR automation\n"
        )
        output=redact_skill_text(source)
        self.assertNotIn("PRIVATE-MATERIAL-IN-TEST",output)
        self.assertNotIn("verysecretbearertoken12345",output)
        self.assertIn("[REDACTED PRIVATE KEY]",output)
        self.assertIn("Bearer [REDACTED]",output)
        self.assertIn("GitHub PR automation",output)

    def test_known_token_formats_and_secret_assignments(self):
        from skillsense_test.local_model import redact_skill_text
        aws="AKIA"+"A"*16
        github="ghp_"+"x"*32
        openai="sk-proj-"+"y"*40
        source=(f"api_key: {openai}\n"
                f"client_secret = very_secret_value_123456\n"
                f"git_token: {github}\n"
                f"token example = not a secret\n"
                f"ACCESS_KEY={aws}\n")
        output=redact_skill_text(source)
        for secret in (openai,github,aws,"very_secret_value_123456"):
            self.assertNotIn(secret,output)
        self.assertIn("token example = not a secret",output)

    def test_non_secret_skill_instructions_remain_usable(self):
        from skillsense_test.local_model import redact_skill_text
        source="## When to Use\nDecompile an APK with JADX to inspect Android bytecode."
        self.assertEqual(redact_skill_text(source),source)
