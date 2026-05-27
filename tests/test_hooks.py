from __future__ import annotations

import json
import sys
import tempfile
import unittest
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS_DIR = ROOT / "hooks"


def _make_status_json(chapter_dir: Path, stage: str, p0: int, p1: int,
                      next_allowed: str) -> None:
    chapter_dir.mkdir(parents=True, exist_ok=True)
    status = {
        "stage": stage,
        "chapter": chapter_dir.name,
        "timestamp": "2026-05-25T12:00:00",
        "p0_count": p0,
        "p1_count": p1,
        "p2_count": 0,
        "green_paragraphs": [],
        "blocked_paragraphs": [],
        "next_allowed": next_allowed,
        "notes": ""
    }
    (chapter_dir / "status.json").write_text(
        json.dumps(status, ensure_ascii=False), encoding="utf-8"
    )


class SessionStartHookTests(unittest.TestCase):
    """session-start 钩子单元测试"""

    def _run_session_start(self, cwd: Path) -> dict:
        result = subprocess.run(
            [sys.executable, str(HOOKS_DIR / "session-start")],
            capture_output=True, text=True, encoding="utf-8", cwd=str(cwd),
        )
        return json.loads(result.stdout)

    def test_no_workflow_dir_returns_default_context(self) -> None:
        """无 .thesis-workflow 时返回默认上下文"""
        with tempfile.TemporaryDirectory() as tmp:
            output = self._run_session_start(Path(tmp))
            ctx = output["hookSpecificOutput"]["additionalContext"]
            self.assertIn("thesis-outline-planner", ctx)

    def test_reports_chapter_progress(self) -> None:
        """存在 status.json 时注入章节进度"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / ".thesis-workflow").mkdir()
            ch_dir = base / ".thesis-workflow" / "chapters" / "ch1"
            _make_status_json(ch_dir, "audited", 0, 0, "humanizer")

            output = self._run_session_start(base)
            ctx = output["hookSpecificOutput"]["additionalContext"]
            self.assertIn("ch1", ctx)

    def test_reports_fix_evidence_when_p0_positive(self) -> None:
        """P0 > 0 时报告 fix-evidence 状态"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / ".thesis-workflow").mkdir()
            ch_dir = base / ".thesis-workflow" / "chapters" / "ch2"
            _make_status_json(ch_dir, "audited", 2, 1, "fix-evidence")

            output = self._run_session_start(base)
            ctx = output["hookSpecificOutput"]["additionalContext"]
            self.assertIn("fix-evidence", ctx)


class PreToolUseHookTests(unittest.TestCase):
    """pre-tool-use 钩子单元测试"""

    def _run(self, tool_name: str, file_path: str, cwd: Path) -> dict:
        """模拟 Claude Code 调用 pre-tool-use 钩子（通过 stdin 传 JSON）"""
        input_data = json.dumps({
            "tool_name": tool_name,
            "tool_input": {"file_path": file_path},
        })
        result = subprocess.run(
            [sys.executable, str(HOOKS_DIR / "pre-tool-use")],
            input=input_data, capture_output=True, text=True, encoding="utf-8",
            cwd=str(cwd),
        )
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def test_blocks_main_file_without_full_completion(self) -> None:
        """主文件 next_allowed != next-chapter 时拒绝写入"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / ".thesis-workflow").mkdir()
            ch_dir = base / ".thesis-workflow" / "chapters" / "ch1"
            _make_status_json(ch_dir, "audited", 0, 0, "humanizer")

            output = self._run("Write", str(base / "main-ch1.md"), base)
            decision = output.get("hookSpecificOutput", {}).get("permissionDecision", "")
            self.assertEqual(decision, "deny")

    def test_allows_main_file_when_next_chapter(self) -> None:
        """next_allowed == next-chapter 时不阻止写入"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / ".thesis-workflow").mkdir()
            ch_dir = base / ".thesis-workflow" / "chapters" / "ch1"
            _make_status_json(ch_dir, "format-cleaned", 0, 0, "next-chapter")

            output = self._run("Write", str(base / "main-ch1.md"), base)
            self.assertNotIn("deny", output.get("hookSpecificOutput", {}).get(
                "permissionDecision", ""))

    def test_blocks_humanizer_when_p0_not_zero(self) -> None:
        """P0 > 0 时拒绝 humanized.md 写入（使用相对路径，匹配 Claude Code 行为）"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / ".thesis-workflow").mkdir()
            ch_dir = base / ".thesis-workflow" / "chapters" / "ch3"
            _make_status_json(ch_dir, "audited", 1, 0, "fix-evidence")

            # Claude Code 传入的是相对路径（正斜杠）
            output = self._run(
                "Write",
                ".thesis-workflow/chapters/ch3/humanized.md",
                base,
            )
            decision = output.get("hookSpecificOutput", {}).get("permissionDecision", "")
            self.assertEqual(decision, "deny")

    def test_allows_draft_when_no_status(self) -> None:
        """无 status.json 时不阻止 draft.md 写入（防线不匹配则放行）"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / ".thesis-workflow").mkdir()
            (base / ".thesis-workflow" / "chapters" / "ch1").mkdir(parents=True)
            # 防线 3 会检查上游产物 outline.md 是否存在，补充它以隔离"仅缺 status.json"的条件
            (base / ".thesis-workflow" / "outline.md").touch()

            output = self._run(
                "Write",
                str(base / ".thesis-workflow/chapters/ch1/draft.md"),
                base,
            )
            self.assertEqual(output, {})

    def test_ignores_non_write_tools(self) -> None:
        """非 Write/Edit/MultiEdit 工具直接放行"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / ".thesis-workflow").mkdir()
            ch_dir = base / ".thesis-workflow" / "chapters" / "ch1"
            _make_status_json(ch_dir, "audited", 1, 0, "fix-evidence")

            output = self._run("Read", str(base / "main-ch1.md"), base)
            self.assertEqual(output, {})


if __name__ == "__main__":
    unittest.main()
