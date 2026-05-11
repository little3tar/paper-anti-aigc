# -*- coding: utf-8 -*-
"""check_text.py 与 check_format.py 的共享工具函数。

本模块提取两个 checker 中完全重复的辅助函数，避免维护两份副本。
修改任一函数时只需改此处，两个 checker 同步生效。
"""

from __future__ import annotations

import re
import io
import os
import sys
from pathlib import Path

# ── Windows GBK 兼容 ──────────────────────────────────────


def setup_windows_utf8() -> None:
    """强制 stdout/stderr 使用 UTF-8（Windows GBK 终端兼容）。"""
    if os.name == "nt":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ── LaTeX 环境检测 ─────────────────────────────────────────


def is_in_math_env(line: str, match_start: int) -> bool:
    r"""粗略判断匹配位置是否处于行内数学环境内部（仅 LaTeX）

    支持: $...$, $$...$$, \(...\), \[...\]
    """
    # 检查 \(...\) 和 \[...\]
    for opener, closer in [(r"\(", r"\)"), (r"\[", r"\]")]:
        search_start = 0
        while True:
            op = line.find(opener, search_start)
            if op == -1 or op >= match_start:
                break
            cl = line.find(closer, op + len(opener))
            if cl == -1:
                # 未闭合，match_start 在 opener 之后 → 视为数学环境内
                if match_start > op:
                    return True
                break
            if op < match_start <= cl:
                return True
            search_start = cl + len(closer)

    # 检查 $...$ 和 $$...$$ (用未转义的 $ 做 toggle)
    dollars = [m.start() for m in re.finditer(r"(?<!\\)\$", line)]
    depth = 0
    for d in dollars:
        if d >= match_start:
            break
        depth += 1
    return depth % 2 == 1


def precompute_block_math(lines: list[str]) -> list[bool]:
    """预计算每一行是否处于块级数学环境内（仅 LaTeX）"""
    math_envs = (
        "equation",
        "align",
        "gather",
        "multline",
        "eqnarray",
        "math",
        "displaymath",
    )
    begin_pats = [re.compile(rf"\\begin\{{{env}\*?\}}") for env in math_envs]
    end_pats = [re.compile(rf"\\end\{{{env}\*?\}}") for env in math_envs]
    depth = 0
    result = []
    for line in lines:
        had_begin = False
        for bp, ep in zip(begin_pats, end_pats):
            begins = len(bp.findall(line))
            ends = len(ep.findall(line))
            if begins > 0:
                had_begin = True
            depth += begins
            depth -= ends
        # 同行包含 begin 时，该行也视为数学环境内部
        result.append(depth > 0 or had_begin)
    return result


def precompute_protected_envs(lines: list[str]) -> list[bool]:
    """预计算每一行是否处于受保护的 LaTeX 环境内

    代码、绘图和纯数据表格环境内的 AIGC/PUNCT/STYLE 规则应被跳过（仅检查 CITE/LATEX）。
    不保护 figure/table 外层环境，因为 caption 和表格说明通常是正文的一部分。
    """
    protected_envs = ("tikzpicture", "verbatim", "lstlisting", "minted", "tabular", "tabularx")
    begin_pats = [re.compile(rf"\\begin\{{{env}\*?\}}") for env in protected_envs]
    end_pats = [re.compile(rf"\\end\{{{env}\*?\}}") for env in protected_envs]
    depth = 0
    result = []
    for line in lines:
        had_begin = False
        for bp, ep in zip(begin_pats, end_pats):
            begins = len(bp.findall(line))
            ends = len(ep.findall(line))
            if begins > 0:
                had_begin = True
            depth += begins
            depth -= ends
        # 同行包含 begin 时，该行也视为受保护环境内部
        result.append(depth > 0 or had_begin)
    return result


def precompute_markdown_protected(lines: list[str]) -> list[bool]:
    """预计算 Markdown/YAML frontmatter 和 fenced code block 行。"""
    result = [False] * len(lines)

    # YAML frontmatter: 仅当文件第一行是 --- 时启用
    if lines and lines[0].strip() == "---":
        result[0] = True
        for i in range(1, len(lines)):
            result[i] = True
            if lines[i].strip() == "---":
                break

    in_fence = False
    fence_marker = None
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
                result[i] = True
                continue
            if marker == fence_marker:
                result[i] = True
                in_fence = False
                fence_marker = None
                continue
        if in_fence:
            result[i] = True
    return result


# ── 遮蔽函数 ───────────────────────────────────────────────


def mask_inline_code(line: str) -> str:
    """用空格遮蔽 Markdown 行内代码和 HTML 标签，保留列号基本稳定。"""
    def repl(match: re.Match) -> str:
        return " " * (match.end() - match.start())

    line = re.sub(r"`[^`\n]+`", repl, line)
    return re.sub(r"<[^>\n]+>", repl, line)


def mask_latex_inline_protected(line: str) -> str:
    r"""遮蔽 LaTeX 正文行内的代码、路径和链接命令。

    文本 humanizer 需要检查中文正文，但不应把 \texttt{"x"}、\url{...}、
    \href{...}{...} 或 \verb|...| 中的引号和 dash 当成正文标点。
    这里做轻量遮蔽，避免为了标点检查误伤命令参数。
    """

    def repl(match: re.Match) -> str:
        return " " * (match.end() - match.start())

    line = re.sub(r"\\verb\*?(.).*?\1", repl, line)
    return re.sub(
        r"\\(?:texttt|url|path|href)\b(?:\[[^\]]*\])?\{[^{}\n]*\}(?:\{[^{}\n]*\})?",
        repl,
        line,
    )


# ── Markdown 行类型判断 ─────────────────────────────────────


def is_markdown_table_separator(line: str) -> bool:
    """Return True for Markdown table separator rows such as ``| --- | :---: |``."""
    stripped = line.strip()
    return bool(
        re.fullmatch(r"\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?", stripped)
    )


def is_markdown_structured_row(line: str) -> bool:
    """Return True for Markdown rows/lists where enumeration noise is expected."""
    stripped = line.lstrip()
    return bool(
        stripped.startswith("|")
        or re.match(r"^(?:[-*+]|\d+[.)])\s+", stripped)
    )


# ── Dash 上下文判断 ────────────────────────────────────────


def is_allowed_dash_context(line: str, start: int, end: int) -> bool:
    """判断 dash 是否属于数字范围、页码范围或技术记号。"""
    token = line[start:end]
    prev_char = line[start - 1] if start > 0 else ""
    next_char = line[end] if end < len(line) else ""

    if token in {"–", "--", "---"}:
        if prev_char.isdigit() and next_char.isdigit():
            return True
        if prev_char.isascii() and prev_char.isalnum() and next_char.isascii() and next_char.isalnum():
            return True
    return False


# ── LaTeX 注释剥离 ─────────────────────────────────────────


def strip_latex_comment(line: str) -> str:
    """剥离 LaTeX 行内注释，返回处理后的行

    截断 % 后的内容，但保留转义的 \\% 或 \\%{} 等。
    """
    # 找到第一个未转义的 %
    # 排除 \% 和 \%{ 的情况
    result = []
    i = 0
    while i < len(line):
        # 检查 \% 或 \%{ (转义的百分号)
        if i < len(line) - 1 and line[i] == "\\" and line[i + 1] == "%":
            result.append("\\%")
            i += 2
        elif (
            i < len(line) - 2
            and line[i] == "\\"
            and line[i + 1] == "%"
            and line[i + 2] == "{"
        ):
            result.append("\\%{")
            i += 3
        elif line[i] == "%":
            # 遇到未转义的 %，截断后面所有内容
            break
        else:
            result.append(line[i])
            i += 1
    return "".join(result)


# ── 输出格式化 ─────────────────────────────────────────────


SEVERITY_ICONS = {
    "error": "[ERROR]",
    "warning": "[WARN]",
    "info": "[INFO]",
}


def format_text(diagnostics: list[dict], filepath: str) -> str:
    """格式化为人类可读的文本报告"""
    if not diagnostics:
        return f"[OK] {filepath}: 未发现问题"

    counts: dict[str, int] = {"error": 0, "warning": 0, "info": 0}
    lines = []
    lines.append(f"{'=' * 60}")
    lines.append(f"  检查文件: {filepath}")
    lines.append(f"{'=' * 60}")

    for d in diagnostics:
        sev = d.get("severity", "info")
        counts[sev] = counts.get(sev, 0) + 1
        icon = SEVERITY_ICONS.get(sev, f"[{sev.upper()}]")
        lines.append(f"")
        lines.append(f"{icon} [{d['rule']}] L{d['line']}:{d['column']}  {d['message']}")
        lines.append(f"   上下文: {d['context'][:80]}")
        lines.append(f"   修复建议: {d['fix']}")

    lines.append(f"")
    lines.append(f"{'=' * 60}")
    lines.append(
        f"  汇总: {counts['error']} 错误 | {counts['warning']} 警告 | {counts['info']} 提示"
    )
    lines.append(f"{'=' * 60}")

    return "\n".join(lines)
