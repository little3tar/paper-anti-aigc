# -*- coding: utf-8 -*-
"""check_text.py / check_format.py / generate_dict / generate_format_dict 的共享工具函数。

本模块提取 checker 和 dict 生成器中完全重复的辅助函数，避免维护多份副本。
修改任一函数时只需改此处，所有调用方同步生效。
"""

from __future__ import annotations

import re
import io
import os
import sys
from pathlib import Path

# ── Windows GBK 兼容 ──────────────────────────────────────


def setup_windows_utf8() -> None:
    """强制 stdout/stderr 使用 UTF-8（Windows GBK 终端兼容）。

    在 pytest、IDE 控制台等非标准输出环境下静默回退，避免 AttributeError。
    """
    if os.name != "nt":
        return
    for attr in ("stdout", "stderr"):
        stream = getattr(sys, attr)
        try:
            setattr(sys, attr, io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace"))
        except (AttributeError, ValueError):
            pass


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
        re.fullmatch(r"\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)+\|?", stripped)
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
    # 注意：start = 0 时显式返回空串，避免 Python 负索引环绕读取行末字符
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


# ── 规则速查表生成（generate_dict / generate_format_dict 共享） ──

import json  # noqa: E402


def _categorize_rules(rules: list[dict]) -> dict[str, list[dict]]:
    """按规则 ID 前缀分组（与 rules JSON 保持一致，无硬编码）"""
    PREFIX_MAP = {
        "CITE": "引用格式问题（LaTeX）",
        "LATEX": "LaTeX 专属问题",
        "PUNCT": "标点与格式问题",
        "STYLE": "排版风格问题",
        "AIGC": "AI 高频词与敏感短语",
    }

    categories: dict[str, list[dict]] = {}
    for rule in rules:
        rule_id = rule.get("id", "")
        prefix = rule_id.split("-")[0] if "-" in rule_id else rule_id
        cat_name = PREFIX_MAP.get(prefix, "其他")
        categories.setdefault(cat_name, []).append(rule)

    return {k: v for k, v in categories.items() if v}


def _format_rule_table(rules: list[dict], header_left: str, header_right: str) -> str:
    """生成 Markdown 规则表格。header_left/header_right 为表头两列名。"""

    def code_cell(value: str) -> str:
        value = str(value).replace("\n", " ")
        value = value.replace("`", "\\`").replace("|", "\\|")
        return f"`{value}`"

    lines = []
    lines.append(f"| {header_left} | {header_right} | 严重程度 | 适用格式 |")
    lines.append("|-------------------|-----------|----------|----------|")

    for rule in rules:
        pattern = rule.get("pattern", "")
        display_pattern = (
            rule.get("label")
            or rule.get("example")
            or rule.get("examples")
            or rule.get("phrase")
            or pattern
        )
        if isinstance(display_pattern, list):
            display_pattern = " / ".join(str(x) for x in display_pattern[:4])
        if len(str(display_pattern)) > 80:
            display_pattern = str(display_pattern)[:77] + "..."

        message = rule.get("message", "")
        fix = rule.get("fix", "")
        if "替换为" in message:
            match = re.search(r"替换为[「\"']?([^」\"']+)[」\"']?", message)
            if match:
                fix = match.group(1)

        severity = rule.get("severity", "info")
        severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(severity, "⚪")
        formats = rule.get("format", ["latex"])
        format_str = ", ".join(formats)

        lines.append(
            f"| {code_cell(display_pattern)} | {fix} | {severity_icon} {severity} | {format_str} |"
        )

    return "\n".join(lines)


def generate_rule_dict_markdown(
    rules_path: str,
    title: str,
    script_name: str,
    check_script: str,
    header_left: str,
    header_right: str,
    *,
    always_show_connectives: bool = False,
    format_filter: str = "all",
    output_filename: str = "dict.md",
) -> str:
    """从 rules JSON 文件生成人类可读的 Markdown 规则速查表。

    参数：
        rules_path: rules JSON 文件路径
        title: 文档标题（一级标题）
        script_name: 生成脚本名（用于文档引用）
        check_script: 检测脚本名（用于使用说明）
        header_left: 规则表格左侧列名
        header_right: 规则表格右侧列名
        always_show_connectives: 即使 JSON 无 connectives 数据也显示连接词段落
        format_filter: 格式过滤器（\"all\" / \"latex\" / \"markdown\" / \"plain\"）
        output_filename: 使用说明中的示例输出文件名
    """
    rules_data = json.loads(Path(rules_path).read_text(encoding="utf-8-sig"))
    rules: list[dict] = rules_data.get("rules", [])
    connectives: dict = rules_data.get("connectives", {})

    categories = _categorize_rules(rules)

    result = []
    result.append(title)
    result.append("")
    result.append(f"> 本文件由 `scripts/{script_name}` 从 rules JSON 自动生成。")
    result.append(f"> 实际检测请使用 `python scripts/{check_script} <file>`。")
    result.append("")

    # 连接词列表
    has_connectives = connectives and "words" in connectives and connectives["words"]
    if always_show_connectives or has_connectives:
        result.append("## 连接词泛滥检测")
        result.append("")
        result.append("以下连接词在段/句首出现时，建议删除至少 50%：")
        result.append("")
        if has_connectives:
            words = connectives["words"]
            result.append("```")
            for i in range(0, len(words), 8):
                result.append("  " + "  ".join(words[i : i + 8]))
            result.append("```")
        result.append("")

    # 各分类表格
    for cat_name, cat_rules in categories.items():
        if not cat_rules:
            continue
        result.append(f"## {cat_name}")
        result.append("")
        if format_filter != "all":
            filtered = [r for r in cat_rules if format_filter in r.get("format", ["latex"])]
            if not filtered:
                continue
            result.append(f"*（仅显示 {format_filter} 格式相关规则）*")
            result.append("")
            result.append(_format_rule_table(filtered, header_left, header_right))
        else:
            result.append(_format_rule_table(cat_rules, header_left, header_right))
        result.append("")

    # 使用说明
    result.append("## 使用说明")
    result.append("")
    result.append(f"1. **实际检测**：运行 `python scripts/{check_script} <file>`")
    result.append("2. **格式支持**：")
    result.append(f"   - LaTeX: `python scripts/{check_script} paper.tex`")
    result.append(f"   - Markdown: `python scripts/{check_script} paper.md --format markdown`")
    result.append(f"   - 纯文本: `python scripts/{check_script} draft.txt --format plain`")
    result.append(f"3. **重新生成本文件**：`python scripts/{script_name} > {output_filename}`")
    result.append("")
    result.append("---")
    result.append("*生成时间：自动生成，请勿手动编辑*")

    return "\n".join(result)
