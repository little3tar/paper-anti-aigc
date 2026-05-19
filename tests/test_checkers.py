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
            "skills/engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/sample_humanizer.md",
            "--format",
            "markdown",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        # 关键 AIGC 规则均应命中
        for rid in ("AIGC-001", "AIGC-002", "AIGC-007", "AIGC-012", "AIGC-015",
                     "AIGC-022", "AIGC-046", "AIGC-052", "AIGC-061", "AIGC-064"):
            self.assertIn(rid, rule_ids, f"应命中 {rid}")
        # 三段式聚合诊断
        self.assertIn("AIGC-AGG-ERR", rule_ids)
        # 去重验证：AIGC-052 已覆盖的"值得注意的是"不应再报 AIGC-CONN
        conn_hits = [d for d in diagnostics if d["rule"] == "AIGC-CONN"]
        aigc052_lines = {d["line"] for d in diagnostics if d["rule"] == "AIGC-052"}
        for c in conn_hits:
            self.assertNotIn(c["line"], aigc052_lines,
                              f"AIGC-CONN L{c['line']} 不应与 AIGC-052 重叠")

    def test_humanizer_checker_reports_real_ai_report_patterns(self) -> None:
        result = run_script(
            "skills/engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/sample_ai_report_patterns.md",
            "--format",
            "markdown",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        for rid in (
            "AIGC-063",
            "AIGC-065",
            "AIGC-066",
            "AIGC-067",
            "AIGC-068",
            "AIGC-069",
            "AIGC-070",
            "AIGC-071",
            "AIGC-072",
            "AIGC-073",
            "AIGC-074",
            "AIGC-075",
        ):
            self.assertIn(rid, rule_ids, f"应命中 {rid}")

    def test_format_checker_reports_latex_errors(self) -> None:
        result = run_script(
            "skills/academic-format-cleaner/scripts/check_format.py",
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
        result = run_script("skills/academic-format-cleaner/scripts/generate_format_dict.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("generate_format_dict.py > format-dict.md", result.stdout)
        self.assertNotIn("generate_dict.py > dict.md", result.stdout)

    def test_git_snapshot_dry_run_does_not_init_git(self) -> None:
        script = ROOT / "skills/engineering-paper-humanizer/scripts/git_snapshot.py"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target = tmp_path / "paper.md"
            target.write_text("draft", encoding="utf-8")
            result = run_script(str(script), "--dry-run", str(target), cwd=tmp_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((tmp_path / ".git").exists())
            self.assertIn("模拟文件备份", result.stdout)
            self.assertIn("最大保留", result.stdout)

    def test_git_snapshot_uses_git_backup_inside_repo(self) -> None:
        result = run_script(
            "skills/engineering-paper-humanizer/scripts/git_snapshot.py",
            "--dry-run",
            "tests/fixtures/sample_humanizer.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("模拟 Git 备份", result.stdout)


    def test_humanizer_checker_empty_file(self) -> None:
        """空文件不产生诊断。"""
        result = run_script(
            "skills/engineering-paper-humanizer/scripts/check_text.py",
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
            "skills/engineering-paper-humanizer/scripts/check_text.py",
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
            "skills/engineering-paper-humanizer/scripts/check_text.py",
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
            "skills/academic-format-cleaner/scripts/check_format.py",
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
            "skills/academic-format-cleaner/scripts/check_format.py",
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
            "skills/academic-format-cleaner/scripts/check_format.py",
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
            "skills/engineering-paper-humanizer/scripts/check_text.py",
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
            "skills/engineering-paper-humanizer/scripts/git_snapshot.py",
            "--cleanup",
            "--dry-run",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("模拟清理", result.stdout)

    def test_git_snapshot_anchor_creates_marker(self) -> None:
        """--anchor 创建锚点备份并生成 .anchor 标记文件。"""
        script = ROOT / "skills/engineering-paper-humanizer/scripts/git_snapshot.py"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target = tmp_path / "paper.md"
            target.write_text("draft v1", encoding="utf-8")
            result = run_script(str(script), "--anchor", str(target), cwd=tmp_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("锚点备份", result.stdout)
            backup_dir = tmp_path / ".thesis-workflow" / "backups"
            anchors = list(backup_dir.glob("*.anchor"))
            self.assertGreater(len(anchors), 0, "锚点标记文件未创建")

    def test_git_snapshot_max_backups_cli(self) -> None:
        """--max-backups 参数可配置最大保留数。"""
        script = ROOT / "skills/engineering-paper-humanizer/scripts/git_snapshot.py"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target = tmp_path / "paper.md"
            for i in range(7):
                target.write_text(f"draft v{i}", encoding="utf-8")
                run_script(str(script), "--max-backups", "3", str(target), cwd=tmp_path)
            backup_dir = tmp_path / ".thesis-workflow" / "backups"
            backups = list(backup_dir.glob("paper_*"))
            self.assertLessEqual(len(backups), 3, f"应保留最多3个备份，实际: {len(backups)}")

    def test_git_snapshot_anchor_immune_to_eviction(self) -> None:
        """锚点备份不受自动淘汰影响。"""
        script = ROOT / "skills/engineering-paper-humanizer/scripts/git_snapshot.py"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target = tmp_path / "paper.md"
            target.write_text("anchor version", encoding="utf-8")
            run_script(str(script), "--anchor", "--max-backups", "1", str(target), cwd=tmp_path)
            for i in range(3):
                target.write_text(f"regular v{i}", encoding="utf-8")
                run_script(str(script), "--max-backups", "1", str(target), cwd=tmp_path)
            backup_dir = tmp_path / ".thesis-workflow" / "backups"
            anchors = list(backup_dir.glob("*.anchor"))
            self.assertGreater(len(anchors), 0, "锚点备份不应被淘汰")

    def test_git_snapshot_dedup_across_all(self) -> None:
        """内容去重应对比所有已有备份，非仅最近一次。"""
        script = ROOT / "skills/engineering-paper-humanizer/scripts/git_snapshot.py"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target = tmp_path / "paper.md"
            target.write_text("state A", encoding="utf-8")
            r1 = run_script(str(script), str(target), cwd=tmp_path)
            target.write_text("state B", encoding="utf-8")
            r2 = run_script(str(script), str(target), cwd=tmp_path)
            target.write_text("state A", encoding="utf-8")
            r3 = run_script(str(script), str(target), cwd=tmp_path)
            self.assertIn("内容相同，跳过备份", r3.stdout)

    def test_git_snapshot_rollback_needs_file(self) -> None:
        """--rollback 不带目标文件时应给出提示。"""
        script = ROOT / "skills/engineering-paper-humanizer/scripts/git_snapshot.py"
        result = run_script(str(script), "--rollback")
        self.assertIn("需要指定", result.stdout)

    def test_git_snapshot_rollback_restores_target_file(self) -> None:
        """--rollback 只恢复指定文件，不影响其他文件。"""
        script = ROOT / "skills/engineering-paper-humanizer/scripts/git_snapshot.py"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target = tmp_path / "paper.md"
            other = tmp_path / "other.md"

            target.write_text("original", encoding="utf-8")
            other.write_text("other original", encoding="utf-8")

            run_script(str(script), str(target), cwd=tmp_path)

            target.write_text("modified", encoding="utf-8")
            other.write_text("other modified", encoding="utf-8")

            run_script(str(script), "--rollback", "--yes", str(target), cwd=tmp_path)

            self.assertEqual(target.read_text(encoding="utf-8"), "original")
            self.assertEqual(other.read_text(encoding="utf-8"), "other modified",
                           "其他文件不应被回滚影响")

    def test_plain_text_detects_markdown_headings(self) -> None:
        """TXT-FMT-001: 检测纯文本中残留的 Markdown 标题标记。"""
        result = run_script(
            "skills/academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_md_in_txt.txt",
            "--format",
            "plain",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("TXT-FMT-001", rule_ids)
        self.assertIn("TXT-FMT-002", rule_ids)

    def test_plain_text_detects_markdown_links_and_lists(self) -> None:
        """TXT-FMT-005/TXT-FMT-006: 检测链接和列表标记残留。"""
        result = run_script(
            "skills/academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_md_in_txt.txt",
            "--format",
            "plain",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("TXT-FMT-005", rule_ids)
        self.assertIn("TXT-FMT-006", rule_ids)

    def test_plain_text_detects_markdown_table(self) -> None:
        """TXT-FMT-010: 检测纯文本中残留的表格管道符。"""
        result = run_script(
            "skills/academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_md_in_txt.txt",
            "--format",
            "plain",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("TXT-FMT-010", rule_ids)

    def test_plain_text_detects_fenced_code(self) -> None:
        """TXT-FMT-011: 检测纯文本中残留的代码块围栏。"""
        result = run_script(
            "skills/academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_md_in_txt.txt",
            "--format",
            "plain",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("TXT-FMT-011", rule_ids)

    def test_fix_plain_text_strips_markdown(self) -> None:
        """--fix --format plain 去除 Markdown 格式标记并输出纯文本。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output = tmp_path / "output.txt"
            result = run_script(
                "skills/academic-format-cleaner/scripts/check_format.py",
                "tests/fixtures/sample_md_in_txt.txt",
                "--format",
                "plain",
                "--fix",
                "--output",
                str(output),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.exists())
            text = output.read_text(encoding="utf-8")
            # 纯文本不应包含 Markdown 标记
            self.assertNotIn("**", text)
            self.assertNotIn("##", text)
            self.assertNotIn("[链接文字]", text)
            # 应保留纯文字内容
            self.assertIn("测试标题", text)
            self.assertIn("加粗文字", text)
            # 表格应转换为纯文本格式（空格分隔）
            self.assertIn("参数", text)
            self.assertIn("流量", text)
            self.assertIn("压力", text)
            self.assertIn("100", text)
            self.assertIn("L/min", text)

    def test_fix_plain_text_stdout(self) -> None:
        """--fix --format plain 不指定 --output 时输出到 stdout。"""
        result = run_script(
            "skills/academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_md_in_txt.txt",
            "--format",
            "plain",
            "--fix",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        # stdout 应包含转换后的纯文本
        self.assertIn("测试标题", result.stdout)
        self.assertNotIn("##", result.stdout)

    def test_latex_detects_empty_cite(self) -> None:
        """LATEX-004: 检测空 \\cite{}。"""
        result = run_script(
            "skills/academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_format.tex",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("LATEX-004", rule_ids)

    def test_latex_detects_unescaped_underscore(self) -> None:
        """LATEX-005: 检测中文正文中未转义的下划线。"""
        result = run_script(
            "skills/academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_format.tex",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("LATEX-005", rule_ids)

    def test_latex_detects_unescaped_ampersand(self) -> None:
        """LATEX-006: 检测中文正文中未转义的 & 符号。"""
        result = run_script(
            "skills/academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_format.tex",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("LATEX-006", rule_ids)

    def test_latex_detects_missing_label(self) -> None:
        """LATEX-007: 检测 \\section{} 后缺少 \\label{}。"""
        result = run_script(
            "skills/academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_format.tex",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("LATEX-007", rule_ids)

    def test_latex_detects_empty_item(self) -> None:
        """STYLE-004: 检测空 \\item 行。"""
        result = run_script(
            "skills/academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_format.tex",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("STYLE-004", rule_ids)

    def test_latex_detects_begin_end_mismatch(self) -> None:
        """LATEX-008: 检测 \\begin{} 与 \\end{} 不匹配。"""
        result = run_script(
            "skills/academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_format.tex",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("LATEX-008", rule_ids)

    def test_generate_format_dict_includes_all_rules(self) -> None:
        """generate_format_dict.py 应包含所有规则类别，包括纯文本和新增 LaTeX 规则。"""
        result = run_script("skills/academic-format-cleaner/scripts/generate_format_dict.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("plain", result.stdout)
        self.assertIn("latex", result.stdout)
        self.assertIn("其他", result.stdout)

    # ── PUNCT 规则 ─────────────────────────────────────────

    def test_humanizer_detects_ascii_quotes(self) -> None:
        """PUNCT-001: 检测中文正文中的 ASCII 直双引号。"""
        result = run_script(
            "skills/engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/sample_punct.md",
            "--format", "markdown", "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("PUNCT-001", rule_ids)

    def test_humanizer_detects_em_dash(self) -> None:
        """PUNCT-002: 检测中文正文中的破折号/异常 dash。"""
        result = run_script(
            "skills/engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/sample_punct.md",
            "--format", "markdown", "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("PUNCT-002", rule_ids)

    def test_humanizer_parentheses_policy(self) -> None:
        """PUNCT-007: 中文解释括号应清理，英文全称/参数括号可保留。"""
        result = run_script(
            "skills/engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/sample_parentheses_policy.md",
            "--format", "markdown", "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        punct_hits = [item for item in diagnostics if item["rule"] == "PUNCT-007"]
        self.assertEqual(len(punct_hits), 2, punct_hits)
        contexts = "\n".join(item["context"] for item in punct_hits)
        self.assertIn("教材式解释括号", contexts)
        self.assertIn("检查同步性", contexts)
        self.assertNotIn("Oscillating Disc Cutting", contexts)
        self.assertNotIn("31.5 MPa", contexts)

    def test_humanizer_no_punct_in_latex_comments(self) -> None:
        """LaTeX 注释行内的标点不应触发 PUNCT 规则。"""
        result = run_script(
            "skills/engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/sample_multisection.tex",
            "--section", "2", "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        # 第 2 节是注释区，不应有大量诊断
        self.assertLessEqual(len(diagnostics), 5,
                             f"注释区内诊断应很少，实际: {len(diagnostics)}")

    # ── 连接词泛滥检测 ────────────────────────────────────

    def test_humanizer_connective_detection(self) -> None:
        """AIGC-CONN: 检测段首/句首连接词泛滥。"""
        result = run_script(
            "skills/engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/sample_humanizer.md",
            "--format", "markdown", "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        # sample_humanizer.md 中"值得注意的是"被 AIGC-052 覆盖，不应重复报 CONN
        self.assertNotIn("AIGC-CONN", rule_ids,
                         "被 AIGC 规则覆盖的词不应再报 AIGC-CONN")

    # ── burstiness 粗评 ────────────────────────────────────

    def test_humanizer_burstiness_no_false_positive(self) -> None:
        """BURST-001: 短段落不应误报 burstiness 警告。"""
        # sample_humanizer.md 只有 5 行，不够触发 BURST-001
        result = run_script(
            "skills/engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/sample_humanizer.md",
            "--format", "markdown", "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertNotIn("BURST-001", rule_ids,
                         "短文不应触发段内句长方差警告")

    # ── 引号平衡检测 ──────────────────────────────────────

    def test_humanizer_quote_balance(self) -> None:
        """PUNCT-005/PUNCT-006: 检测引号不平衡。"""
        result = run_script(
            "skills/engineering-paper-humanizer/scripts/check_text.py",
            "tests/fixtures/sample_punct.md",
            "--format", "markdown", "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        # 第 7 行有引号不平衡（左引号缺失），应触发 PUNCT-005 或 PUNCT-006
        self.assertTrue(
            "PUNCT-005" in rule_ids or "PUNCT-006" in rule_ids,
            f"引号不平衡行应触发 PUNCT-005 或 PUNCT-006，实际命中: {rule_ids}",
        )

    # ── generate_dict ──────────────────────────────────────

    def test_generate_dict_includes_all_categories(self) -> None:
        """generate_dict.py 应包含所有规则类别。"""
        result = run_script("skills/engineering-paper-humanizer/scripts/generate_dict.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AI 高频词与敏感短语", result.stdout)
        self.assertIn("标点与格式问题", result.stdout)
        self.assertIn("连接词泛滥检测", result.stdout)

    # ── CITE 规则补充 ─────────────────────────────────────

    def test_format_detects_cite_not_after_period(self) -> None:
        """CITE-001: 检测句号后 \\cite{}（应移到句号前）。"""
        result = run_script(
            "skills/academic-format-cleaner/scripts/check_format.py",
            "tests/fixtures/sample_format.tex",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = json.loads(result.stdout)
        rule_ids = {item["rule"] for item in diagnostics}
        self.assertIn("CITE-001", rule_ids)


if __name__ == "__main__":
    unittest.main()
