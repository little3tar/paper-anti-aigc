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


    def test_humanizer_checker_empty_file(self) -> None:
        """空文件不产生诊断。"""
        result = run_script(
            "engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/empty.md",
            "--format",
            "markdown",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        self.assertEqual(diagnostics, [])

    def test_humanizer_checker_section_filter(self) -> None:
        """--section 参数只检查指定章节。"""
        result = run_script(
            "engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/sample_multisection.tex",
            "--section",
            "1",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        # 第 1 章有 "本章介绍了" 应触发 AIGC-001
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("AIGC-001", rule_ids)

    def test_humanizer_checker_severity_filter(self) -> None:
        """--severity error 只返回 error 级别诊断。"""
        result = run_script(
            "engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/sample_humanizer.md",
            "--format",
            "markdown",
            "--json",
            "--severity",
            "error",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        for d in diagnostics:
            self.assertEqual(d["severity"], "error")

    def test_format_checker_markdown_math_style(self) -> None:
        """MD-MATH-001: 检测 Markdown 混合数学格式。"""
        result = run_script(
            "academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_mixed_math.md",
            "--format",
            "markdown",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("MD-MATH-001", rule_ids)

    def test_format_checker_evidence_gap_marker(self) -> None:
        """MD-SOURCE-001: 检测正文中残留的证据缺口标记。"""
        result = run_script(
            "academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_evidence_gap.md",
            "--format",
            "markdown",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("MD-SOURCE-001", rule_ids)

    def test_format_checker_no_aigc_conn(self) -> None:
        """格式检查器不应报告 AIGC-CONN（连接词检测属于 humanizer）。"""
        result = run_script(
            "academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_humanizer.md",
            "--format",
            "markdown",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertNotIn("AIGC-CONN", rule_ids)

    def test_humanizer_checker_json_output(self) -> None:
        """--json 输出为有效 JSON 且包含必要字段。"""
        result = run_script(
            "engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/sample_humanizer.md",
            "--format",
            "markdown",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        self.assertIsInstance(diagnostics, list)
        if diagnostics:
            d = diagnostics[0]
            for key in ("line", "column", "rule", "severity", "message", "fix", "context"):
                self.assertIn(key, d)

    def test_git_snapshot_cleanup_dry_run(self) -> None:
        """--cleanup --dry-run 不实际删除任何备份。"""
        result = run_script(
            "engineering-paper-humanizer/scripts/git_snapshot.py",
            "--cleanup",
            "--dry-run",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("模拟清理", result.stdout)


if __name__ == "__main__":
    unittest.main()
