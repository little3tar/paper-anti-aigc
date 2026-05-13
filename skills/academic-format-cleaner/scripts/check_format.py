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

# 查找 _shared 模块：从当前脚本向上搜索，找到 skills 根目录下的 engineering-paper-humanizer/scripts
_script_dir = Path(__file__).resolve().parent
_shared_dir = None
for _root_candidate in _script_dir.parents:
    _candidate = _root_candidate / "engineering-paper-humanizer" / "scripts"
    if _candidate.is_dir():
        _shared_dir = _candidate
        break
if _shared_dir is None:
    # 回退到原来的硬编码路径（保持向后兼容）
    _shared_dir = Path(__file__).resolve().parents[2] / "engineering-paper-humanizer" / "scripts"
sys.path.insert(0, str(_shared_dir))
from _shared import (  # noqa: E402
    is_in_math_env,
    precompute_block_math,
    precompute_protected_envs,
    precompute_markdown_protected,
    mask_inline_code,
    strip_latex_comment,
    is_markdown_table_separator,
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


def check_evidence_gaps(lines: list[str], start: int, end: int) -> list[dict]:
    """标记正文中残留的证据缺口/待补来源标记（适用所有格式）。"""
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


def _convert_md_table_block(lines: list[str]) -> list[str]:
    """将 Markdown 表格块转换为纯文本表示。

    窄表格（≤3 列）按行转为 key-value 列表；宽表格转为对齐文本。
    无法解析时返回 [表格] 占位标记。
    """
    rows: list[list[str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or is_markdown_table_separator(stripped):
            continue
        cells = [c.strip() for c in stripped.split("|")]
        if cells and not cells[0]:
            cells = cells[1:]
        if cells and not cells[-1]:
            cells = cells[:-1]
        if cells:
            rows.append(cells)

    if not rows:
        return ["[表格: 无内容]"]

    # 窄表格（≤3 列）：逐行 key-value
    if len(rows) >= 2 and len(rows[0]) <= 2:
        result: list[str] = []
        header = rows[0]
        for row in rows[1:]:
            for j, cell in enumerate(row):
                if j < len(header):
                    result.append(f"  {header[j]}: {cell}")
            result.append("")
        return result

    # 宽表格：单空格分隔，每行末尾无空格
    result: list[str] = []
    for row in rows:
        result.append(" ".join(row).rstrip())
    result.append("")
    return result


def _is_chart_block(fence_lang: str) -> bool:
    """判断是否为图表代码块（Mermaid / Python matplotlib / Graphviz DOT）。"""
    lang = fence_lang.strip().lower()
    if lang in ("mermaid", "dot", "graphviz"):
        return True
    if "mermaid" in lang or "dot" in lang:
        return True
    return False


def strip_to_plain_text(text: str) -> str:
    """将 Markdown 文本转换为纯文本，去除所有 Markdown 格式标记。

    处理范围：
    - 标题 # → 纯文字标题
    - 加粗 **text** / 斜体 *text* → 去除标记
    - 行内代码 `code` → 去除反引号
    - 链接 [text](url) → 保留文字
    - 图片 ![alt](url) → [图片: alt]
    - 列表标记 - / * / 1. → 去除标记
    - 引用 > → 去除标记
    - 代码块围栏 → 去除围栏
    - 水平线 → 空行
    - 表格 → 调用 _convert_md_table_block 转换
    """
    lines = text.splitlines()
    result: list[str] = []
    i = 0
    # 初始化图表标志
    fence_is_chart = False
    in_fence = False
    fence_marker = ""
    in_table = False
    table_start = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 处理代码块围栏（含引用块内围栏 > ```）
        fence_match = re.match(r"^(> )?\s*(```|~~~)", stripped)
        if fence_match:
            marker = fence_match.group(2)
            if not in_fence:
                fence_lang = stripped[fence_match.end():].strip().lower()
                is_chart = _is_chart_block(fence_lang)
                if is_chart:
                    result.append(f"[图表代码：{fence_lang} — 可在对应工具中渲染]")
                in_fence = True
                fence_marker = marker
                fence_is_chart = is_chart
                if is_chart:
                    result.append(re.sub(r"^>\s?", "", line, count=1))
                i += 1
                continue
            elif marker == fence_marker:
                if fence_is_chart:
                    result.append(re.sub(r"^>\s?", "", line, count=1))
                in_fence = False
                fence_marker = ""
                fence_is_chart = False
                i += 1
                continue

        if in_fence:
            if fence_is_chart:
                result.append(re.sub(r"^>\s?", "", line, count=1))
            else:
                result.append(line)
            i += 1
            continue

        # 检测表格行（累积后批量转换）
        if stripped.startswith("|") and "|" in stripped[1:]:
            if not in_table:
                in_table = True
                table_start = i
            i += 1
            continue
        elif in_table:
            in_table = False
            table_lines = lines[table_start:i]
            result.extend(_convert_md_table_block(table_lines))
            # 表格后不额外加空行，_convert_md_table_block 已处理
            continue

        # 水平线 → 空行
        if re.match(r"^(?:-{3,}|\*{3,}|_{3,})\s*$", stripped):
            if result and result[-1] != "":
                result.append("")
            i += 1
            continue

        # 单行转换
        result.append(_strip_md_line(line))
        i += 1

    # 处理文件末尾未闭合的表格
    if in_table:
        table_lines = lines[table_start:]
        result.extend(_convert_md_table_block(table_lines))

    # 清理空行：连续空行合并为一个；仅在一级标题/表格/图表块前保留一个空行
    _heading_pat = re.compile(r"^\d+\s")
    cleaned: list[str] = []
    prev_empty = False
    for j, r_line in enumerate(result):
        is_empty = r_line == ""
        if is_empty:
            if prev_empty:
                continue
            # 检查下一个非空行是否为标题/表格/图表
            next_is_break = False
            for k in range(j + 1, len(result)):
                nxt = result[k]
                if nxt == "":
                    continue
                next_is_break = bool(_heading_pat.match(nxt)) or nxt in ("[表格]",) or nxt.startswith("[图表代码：")
                break
            if next_is_break:
                cleaned.append("")
                prev_empty = True
            else:
                # 非结构分隔的空行，跳过
                prev_empty = False
        else:
            cleaned.append(r_line)
            prev_empty = False

    return "\n".join(cleaned)


def _strip_md_line(line: str) -> str:
    """去除单行 Markdown 格式标记，返回纯文本。"""
    indent = len(line) - len(line.lstrip())
    indent_str = line[:indent]
    stripped = line[indent:]

    # [此处插入表格/图片：...] → 提取标题文字
    ph_match = re.match(r"^\[此处插入(?:表格|图片)：([^\]]+)\]$", stripped)
    if ph_match:
        return ph_match.group(1)

    # 标题：去掉 # 标记，不保留原始缩进
    heading_match = re.match(r"^(#{1,6})\s+(.*?)(?:\s+#{1,6})?\s*$", stripped)
    if heading_match:
        return heading_match.group(2)

    # 引用：去掉 > 标记
    if stripped.startswith(">"):
        content = re.sub(r"^>\s?", "", stripped, count=1)
        return _strip_md_line(indent_str + content)

    # 列表：去掉 - / * / + / 1. 标记
    list_match = re.match(r"^([-*+]|\d+[.)])\s+(.*)", stripped)
    if list_match:
        return indent_str + list_match.group(2)

    # 行内格式处理
    text = stripped

    # 图片 → [图片: alt]
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"[图片: \1]", text)
    # 链接 → 文字
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # 加粗
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    # 斜体
    text = re.sub(r"(?<!\*)\*([^*\s][^*]*[^*\s]|[^*\s])\*(?!\*)", r"\1", text)
    # 行内代码
    text = re.sub(r"`([^`\n]+)`", r"\1", text)

    return indent_str + text


def check_latex_begin_end_pairs(lines: list[str]) -> list[dict]:
    """检测 LaTeX 中 \\begin{...} 与 \\end{...} 不匹配的问题。

    按行扫描，维护环境栈。无法确定匹配关系时（如跨文件引用）不误报。
    """
    diagnostics: list[dict] = []
    begin_end_pat = re.compile(r"\\(begin|end)\{([^}]+)\}")
    stack: list[tuple[str, int]] = []  # (env_name, line_no)

    for i, line in enumerate(lines):
        for m in begin_end_pat.finditer(line):
            cmd, env = m.group(1), m.group(2)
            if cmd == "begin":
                stack.append((env, i + 1))
            else:
                if stack and stack[-1][0] == env:
                    stack.pop()
                elif stack:
                    diagnostics.append({
                        "line": i + 1,
                        "column": m.start() + 1,
                        "rule": "LATEX-008",
                        "severity": "error",
                        "message": (
                            f"\\end{{{env}}} 与前一个 "
                            f"\\begin{{{stack[-1][0]}}} (L{stack[-1][1]}) 不匹配"
                        ),
                        "fix": (
                            f"将 \\end{{{env}}} 改为 \\end{{{stack[-1][0]}}}，"
                            f"或检查环境嵌套顺序"
                        ),
                        "context": line.strip(),
                    })
                # 多余 \end 且栈为空时可能为顶层环境，不误报

    # 未闭合的环境
    for env, line_no in stack:
        diagnostics.append({
            "line": line_no,
            "column": 1,
            "rule": "LATEX-008",
            "severity": "error",
            "message": f"\\begin{{{env}}} 没有对应的 \\end{{{env}}}",
            "fix": f"在合适位置添加 \\end{{{env}}}",
            "context": lines[line_no - 1].strip(),
        })

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
                # 纯文本中图表代码块围栏合法，跳过 TXT-FMT-011
                if rule["id"] == "TXT-FMT-011" and target_format == "plain":
                    sf = line_for_check.strip()
                    if sf.startswith("```mermaid") or sf.startswith("```dot") or sf in ("```",):
                        nearby = any("[图表代码：" in lines[j] for j in range(max(0, i-30), min(len(lines), i+2)))
                        if nearby:
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

    # 证据缺口检查适用所有格式（Markdown/LaTeX/plain text）
    diagnostics.extend(check_evidence_gaps(lines, start_line, end_line))

    if target_format == "latex":
        diagnostics.extend(check_latex_begin_end_pairs(lines))

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
    parser.add_argument(
        "--fix",
        action="store_true",
        help="自动修复可修复的问题。plain 格式：剥离 Markdown 语法；latex 格式：修复百分号转义等",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="修复后输出文件路径（需配合 --fix 使用）。未指定时输出到 stdout",
    )
    args = parser.parse_args()

    # --fix 模式：对 plain 格式执行 Markdown → 纯文本剥离
    if args.fix and args.format == "plain":
        input_path = Path(args.file)
        if not input_path.exists():
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        text = input_path.read_text(encoding="utf-8-sig")
        cleaned = strip_to_plain_text(text)
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(cleaned, encoding="utf-8")
            print(f"[OK] 已生成纯文本: {output_path}", file=sys.stderr)
            # 对输出文件再跑一次检查，验证剥离质量
            diagnostics = check_file(str(output_path), "plain", args.section)
            if diagnostics:
                print(
                    f"[WARN] 输出文件仍有 {len(diagnostics)} 个格式问题，建议手动复查",
                    file=sys.stderr,
                )
        else:
            print(cleaned)
        return

    # 常规检查模式
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
