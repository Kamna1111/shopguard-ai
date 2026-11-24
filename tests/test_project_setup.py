"""Small checks that protect the repository scaffold during early development."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProjectSetupTests(unittest.TestCase):
    def test_planned_top_level_folders_exist(self) -> None:
        expected = (
            "apps/api",
            "apps/web",
            "automation/api",
            "automation/ui",
            "automation/ai",
            "automation/performance",
            "data/knowledge_base",
            "docs/architecture",
            "docs/development",
        )
        for relative_path in expected:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_dir())

    def test_env_example_does_not_contain_a_real_ai_key(self) -> None:
        env_text = (ROOT / ".env.example").read_text(encoding="utf-8")
        api_key_lines = [
            line.split("=", maxsplit=1)[1].strip()
            for line in env_text.splitlines()
            if line.startswith("OPENAI_API_KEY=")
        ]
        self.assertEqual(api_key_lines, [""])

    def test_env_example_is_not_ignored_by_git(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("!.env.example", gitignore)


if __name__ == "__main__":
    unittest.main()
