#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""academic-format-cleaner 格式检查脚本

扫描 LaTeX (.tex)、Markdown (.md) 或纯文本文件，检测文件格式、引用位置、
LaTeX 命令和 Markdown/列表结构等格式问题。正文去 AI 化和通用中文标点问题
由 engineering-paper-humanizer 负责。
输出结构化的逐行诊断结果，供 agent 或人工快速定位修复。

用法:
    python3 scripts/check_format.py <file.tex>                    # LaTeX 文件（默认）
    python3 scripts/check_format.py <file.md> --format markdown   # Markdown 文件
    python3 scripts/check_format.py <file.txt> --format plain     # 纯文本文件
    python3 scripts/check_format.py <file.tex> --section 3        # 只检查指定章节
    python3 scripts/check_format.py <file.tex> --json             # JSON 格式输出
    python3 scripts/check_format.py <file.tex> --severity error   # 只显示错误
"""

from __future__ import annotations

import re
import sys
import json
import argparse
from pathlib import Path

_shared_dir = Path(__file__).resolve().parents[2] / "engineering-paper-humanizer" / "scripts"
sys.path.insert(0, str(_shared_dir))
from _shared import (  # noqa: E402
    is_in_math_env,
    precompute_block_math,
    precompute_protected_envs,
    precompute_markdown_protected,
    mask_inline_code,
    strip_latex_comment,
    SEVERITY_ICONS,
    format_text,
    setup_windows_utf8,
)

setup_windows_utf8()

# ── 从 format_rules.json 加载规则 ───────────────────────────


def load_rules(format_filter: str = "latex") -> list[dict]:
    """从 format_rules.json 加载规则，按 format 过滤

    参数:
        format_filter: "latex" | "markdown" | "plain"

    返回:
        rules
    """
    script_dir = Path(__file__).parent
    rules_path = script_dir / "format_rules.json"

    if not rules_path.exists():
        print(f"[ERROR] 规则文件不存在: {rules_path}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(rules_path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"[ERROR] 无法加载 format_rules.json: {e}", file=sys.stderr)
        sys.exit(1)

    # 过滤规则
    all_rules = data.get("rules", [])
    rules = []
    for rule in all_rules:
        formats = rule.get("format", ["latex"])
        if format_filter in formats:
            rules.append(rule)

    return rules


# ── 核心逻辑 ────────────────────────────────────────────────


def check_markdown_math_style(lines: list[str], start: int, end: int) -> list[dict]:
    """Check whether Markdown block math styles are mixed in one file."""
    styles: dict[str, int] = {}
    for i in range(start, end):
        stripped = lines[i].strip()
        if re.match(r"^```(?:math|latex)\b", stripped, re.IGNORECASE):
            styles.setdefault("fenced math", i + 1)
        elif stripped == "$$":
            styles.setdefault("$$", i + 1)
        elif stripped in {r"\[", r"\]"}:
            styles.setdefault(r"\[...\]", i + 1)

    if len(styles) <= 1:
        return []

    first_style, first_line = next(iter(styles.items()))
    return [
        {
            "line": first_line,
            "column": 1,
            "rule": "MD-MATH-001",
            "severity": "warning",
            "message": "Markdown 文件混用了多种块级数学格式",
            "fix": "统一使用一种块级数学格式，例如 fenced math、$$...$$ 或 \\[...\\]，除非模板明确要求混用",
            "context": "、".join(styles.keys()),
        }
    ]


def check_markdown_title_markers(lines: list[str], start: int, end: int) -> list[dict]:
    """Check working citation title markers after [参考文献]."""
    diagnostics = []
    old_marker = re.compile(r"\[参考文献\]。\[引用关键词:\s*[^\]]+\]")
    compact_key = re.compile(r"\[参考文献\]。\[([a-z][a-z0-9_-]{3,})\]")

    for i in range(start, end):
        line = mask_inline_code(lines[i])
        m_old = old_marker.search(line)
        if m_old:
            diagnostics.append(
                {
                    "line": i + 1,
                    "column": m_old.start() + 1,
                    "rule": "MD-CITE-001",
                    "severity": "warning",
                    "message": "工作稿引用标记使用了非题名格式",
                    "fix": "Zotero/local 文献标记使用题名，例如 [参考文献]。[基于神经网络的悬臂式掘进机自适应截割控制系统研究]",
                    "context": lines[i].strip(),
                }
            )
            continue

        m_key = compact_key.search(line)
        if m_key:
            diagnostics.append(
                {
                    "line": i + 1,
                    "column": m_key.start() + 1,
                    "rule": "MD-CITE-002",
                    "severity": "info",
                    "message": "工作稿引用标记疑似使用短 key",
                    "fix": "工作稿优先使用 [文献题名]；同题名时使用 [题名 作者 年份]，最终定稿再转换为正式引用键",
                    "context": lines[i].strip(),
                }
            )

    return diagnostics


def check_markdown_evidence_gaps(lines: list[str], start: int, end: int) -> list[dict]:
    """Flag missing-source markers left in Markdown body text."""
    diagnostics = []
    marker = re.compile(r"\[待补来源(?::[^\]]*)?\]")
    gap_headings = ("未写入正文的待补资料", "证据缺口清单", "待用户补充的信息", "项目台账")
    in_gap_section = False

    for i in range(start, end):
        stripped = lines[i].strip()
        if re.match(r"^#{1,6}\s+", stripped):
            in_gap_section = any(name in stripped for name in gap_headings)

        if in_gap_section:
            continue

        line = mask_inline_code(lines[i])
        m = marker.search(line)
        if m:
            diagnostics.append(
                {
                    "line": i + 1,
                    "column": m.start() + 1,
                    "rule": "MD-SOURCE-001",
                    "severity": "warning",
                    "message": "正文中残留缺来源标记",
                    "fix": "将缺来源事实、参数或结论移出正文，放入“未写入正文的待补资料”“证据缺口清单”或项目台账",
                    "context": lines[i].strip(),
                }
            )

    return diagnostics


def check_file(
    filepath: str, target_format: str = "latex", section: int | None = None
) -> list[dict]:
    """执行全部检查规则，返回诊断列表

    参数:
        filepath: 文件路径
        target_format: "latex" | "markdown" | "plain"
        section: 只检查指定章节（仅 LaTeX 有效）

    返回:
        诊断列表
    """
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()

    # 加载规则（按 format 过滤）
    rules = load_rules(target_format)

    # 预编译正则表达式（避免每行重复编译）
    for rule in rules:
        rule["_compiled"] = re.compile(rule["pattern"])

    # 数学环境检测（仅 LaTeX）
    if target_format == "latex":
        in_block_math = precompute_block_math(lines)
        # 受保护环境检测（代码、绘图和纯数据表格环境）
        in_protected_env = precompute_protected_envs(lines)
        in_markdown_protected = [False] * len(lines)
    else:
        in_block_math = [False] * len(lines)
        in_protected_env = [False] * len(lines)
        in_markdown_protected = precompute_markdown_protected(lines) if target_format == "markdown" else [False] * len(lines)

    # 如果指定了 section，定位范围（仅 LaTeX）
    start_line, end_line = 0, len(lines)
    if section is not None and target_format == "latex":
        sec_pattern = re.compile(rf"\\section\b")
        sec_positions = []
        for i, line in enumerate(lines):
            if sec_pattern.search(line):
                sec_positions.append(i)
        if section - 1 < len(sec_positions):
            start_line = sec_positions[section - 1]
            end_line = (
                sec_positions[section] if section < len(sec_positions) else len(lines)
            )
        else:
            total = len(sec_positions)
            print(
                f"[WARN] --section {section} 超出范围（共找到 {total} 个 \\section），将扫描全文",
                file=sys.stderr,
            )
    elif section is not None and target_format != "latex":
        print(f"[WARN] --section 参数仅对 LaTeX 文件有效，已忽略", file=sys.stderr)

    diagnostics = []

    # 逐行规则匹配
    for i in range(start_line, end_line):
        line = lines[i]

        # 跳过注释行（LaTeX: %, Markdown/Plain: 无注释语法需跳过）
        stripped = line.lstrip()
        if target_format == "latex" and stripped.startswith("%"):
            continue
        if target_format == "markdown" and in_markdown_protected[i]:
            continue

        # 对 LaTeX 文件剥离行内注释
        if target_format == "latex":
            line_for_check = strip_latex_comment(line)
        elif target_format == "markdown":
            line_for_check = mask_inline_code(line)
        else:
            line_for_check = line

        # 裸百分号本身会截断 LaTeX 行尾，不能等剥离注释后再检查。
        if target_format == "latex":
            for rule in rules:
                if rule["id"] != "LATEX-001":
                    continue
                for m in rule["_compiled"].finditer(line):
                    diagnostics.append(
                        {
                            "line": i + 1,
                            "column": m.start() + 1,
                            "rule": rule["id"],
                            "severity": rule["severity"],
                            "message": rule["message"],
                            "fix": rule["fix"],
                            "context": line.strip(),
                        }
                    )

        # 检查是否在受保护环境内（tikzpicture/table/figure）
        if target_format == "latex" and in_protected_env[i]:
            # 受保护环境内：跳过 AIGC/PUNCT/STYLE 规则，只检查 CITE/LATEX 规则
            for rule in rules:
                if rule["id"] == "LATEX-001":
                    continue
                if rule["id"].startswith(("AIGC", "PUNCT", "STYLE")):
                    continue
                for m in rule["_compiled"].finditer(line_for_check):
                    diagnostics.append(
                        {
                            "line": i + 1,
                            "column": m.start() + 1,
                            "rule": rule["id"],
                            "severity": rule["severity"],
                            "message": rule["message"],
                            "fix": rule["fix"],
                            "context": line.strip(),
                        }
                    )
        # 检查是否在块级数学环境内
        elif in_block_math[i]:
            # 块级数学环境内：跳过 AIGC/PUNCT 规则，CITE/LATEX 规则仍然检查
            for rule in rules:
                if rule["id"] == "LATEX-001":
                    continue
                if rule["id"].startswith(("AIGC", "PUNCT")):
                    continue
                for m in rule["_compiled"].finditer(line_for_check):
                    diagnostics.append(
                        {
                            "line": i + 1,
                            "column": m.start() + 1,
                            "rule": rule["id"],
                            "severity": rule["severity"],
                            "message": rule["message"],
                            "fix": rule["fix"],
                            "context": line.strip(),
                        }
                    )
        else:
            # 普通行：正常检查，但跳过行内数学环境
            for rule in rules:
                if rule["id"] == "LATEX-001":
                    continue
                for m in rule["_compiled"].finditer(line_for_check):
                    if target_format == "latex" and is_in_math_env(
                        line_for_check, m.start()
                    ):
                        continue  # 跳过行内数学环境
                    diagnostics.append(
                        {
                            "line": i + 1,
                            "column": m.start() + 1,
                            "rule": rule["id"],
                            "severity": rule["severity"],
                            "message": rule["message"],
                            "fix": rule["fix"],
                            "context": line.strip(),
                        }
                    )

    if target_format == "markdown":
        diagnostics.extend(check_markdown_math_style(lines, start_line, end_line))
        diagnostics.extend(check_markdown_title_markers(lines, start_line, end_line))
        diagnostics.extend(check_markdown_evidence_gaps(lines, start_line, end_line))

    # 按行号排序
    diagnostics.sort(key=lambda d: (d["line"], d["column"]))
    return diagnostics





# ── 入口 ──────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="academic-format-cleaner 格式检查"
    )
    parser.add_argument("file", help="要检查的文件路径")
    parser.add_argument(
        "--format",
        choices=["latex", "markdown", "plain"],
        default="latex",
        help="文件格式（默认: latex）",
    )
    parser.add_argument(
        "--section",
        type=int,
        default=None,
        help="只检查指定章节编号（按 \\section 出现顺序从 1 计数，仅 LaTeX 有效）",
    )
    parser.add_argument(
        "--json", action="store_true", help="输出 JSON 格式（供 agent 解析）"
    )
    parser.add_argument(
        "--severity",
        default=None,
        choices=["error", "warning", "info"],
        help="只显示指定严重级别及以上",
    )
    args = parser.parse_args()

    diagnostics = check_file(args.file, args.format, args.section)

    # 过滤严重级别
    if args.severity:
        levels = {"error": 3, "warning": 2, "info": 1}
        threshold = levels[args.severity]
        diagnostics = [
            d
            for d in diagnostics
            if levels.get(d.get("severity", "info"), 0) >= threshold
        ]

    if args.json:
        print(json.dumps(diagnostics, ensure_ascii=False, indent=2))
    else:
        print(format_text(diagnostics, args.file))


if __name__ == "__main__":
    main()
