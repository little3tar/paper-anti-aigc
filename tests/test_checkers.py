from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_script(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


class CheckerScriptTests(unittest.TestCase):
    def test_humanizer_checker_reports_aigc_rules(self) -> None:
        result = run_script(
            "engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/sample_humanizer.md",
            "--format",
            "markdown",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("AIGC-001", rule_ids)
        self.assertIn("AIGC-015", rule_ids)

    def test_format_checker_reports_latex_errors(self) -> None:
        result = run_script(
            "academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_format.tex",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("CITE-001", rule_ids)
        self.assertIn("LATEX-001", rule_ids)
        self.assertIn("LATEX-002", rule_ids)

    def test_format_dictionary_usage_points_to_format_generator(self) -> None:
        result = run_script("academic-format-cleaner/scripts/generate_format_dict.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("generate_format_dict.py > format-dict.md", result.stdout)
        self.assertNotIn("generate_dict.py > dict.md", result.stdout)

    def test_git_snapshot_dry_run_does_not_init_git(self) -> None:
        script = ROOT / "engineering-paper-humanizer/scripts/git_snapshot.py"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target = tmp_path / "paper.md"
            target.write_text("draft", encoding="utf-8")
            result = run_script(str(script), "--dry-run", str(target), cwd=tmp_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((tmp_path / ".git").exists())
            self.assertIn("模拟文件备份", result.stdout)
            self.assertIn(".thesis-workflow/backups", result.stdout)

    def test_git_snapshot_uses_git_backup_inside_repo(self) -> None:
        result = run_script(
            "engineering-paper-humanizer/scripts/git_snapshot.py",
            "--dry-run",
            "tests/fixtures/sample_humanizer.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("模拟 Git 备份", result.stdout)


if __name__ == "__main__":
    unittest.main()
