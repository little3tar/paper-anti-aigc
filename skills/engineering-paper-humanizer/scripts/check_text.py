#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""engineering-paper-humanizer 通用中文文本检测脚本

扫描 LaTeX (.tex)、Markdown (.md) 或纯文本文件中的正文内容，检测 AI 腔、
中文标点和通用写作问题。脚本会尽量跳过公式、代码块和命令参数等非正文区域，
但不再报告 LaTeX/Markdown 专属格式问题。
输出结构化的逐行诊断结果，供 agent 或人工快速定位修复。

用法:
    python3 scripts/check_text.py <file.tex>                    # LaTeX 文件（默认）
    python3 scripts/check_text.py <file.md> --format markdown   # Markdown 文件
    python3 scripts/check_text.py <file.txt> --format plain     # 纯文本文件
    python3 scripts/check_text.py <file.tex> --section 3        # 只检查指定章节
    python3 scripts/check_text.py <file.tex> --json             # JSON 格式输出
    python3 scripts/check_text.py <file.tex> --severity error   # 只显示错误
"""

from __future__ import annotations

import re
import sys
import json
import argparse
from pathlib import Path

from _shared import (
    is_in_math_env,
    precompute_block_math,
    precompute_protected_envs,
    precompute_markdown_protected,
    mask_inline_code,
    mask_latex_inline_protected,
    is_markdown_table_separator,
    is_markdown_structured_row,
    is_allowed_dash_context,
    strip_latex_comment,
    format_text,
    setup_windows_utf8,
)

setup_windows_utf8()

# ── 从 text_rules.json 加载规则 ─────────────────────────────


def load_rules(format_filter: str = "latex") -> tuple[list[dict], list[str]]:
    """从 text_rules.json 加载规则和连接词，按 format 过滤

    参数:
        format_filter: "latex" | "markdown" | "plain"

    返回:
        (rules, connectives_words)
    """
    script_dir = Path(__file__).parent
    rules_path = script_dir / "text_rules.json"

    if not rules_path.exists():
        print(f"[ERROR] 规则文件不存在: {rules_path}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(rules_path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"[ERROR] 无法加载 text_rules.json: {e}", file=sys.stderr)
        sys.exit(1)

    # 过滤规则
    all_rules = data.get("rules", [])
    rules = []
    for rule in all_rules:
        formats = rule.get("format", ["latex"])
        if format_filter in formats:
            rules.append(rule)

    # 连接词（如果 format 匹配）
    connectives = data.get("connectives", {})
    connectives_words = []
    if format_filter in connectives.get("format", ["latex", "markdown", "plain"]):
        connectives_words = connectives.get("words", [])

    return rules, connectives_words


# ── 核心逻辑 ────────────────────────────────────────────────





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
    rules, connectives_words = load_rules(target_format)

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
            line_for_check = mask_latex_inline_protected(strip_latex_comment(line))
        elif target_format == "markdown":
            line_for_check = mask_inline_code(line)
        else:
            line_for_check = line

        # 检查是否在受保护环境内（tikzpicture/table/figure）
        if target_format == "latex" and in_protected_env[i]:
            # 受保护环境内：跳过 AIGC/PUNCT/STYLE 规则，只检查 CITE/LATEX 规则
            for rule in rules:
                if rule["id"].startswith(("AIGC", "PUNCT", "STYLE")):
                    continue
                for m in rule["_compiled"].finditer(line_for_check):
                    if rule["id"] == "PUNCT-002" and is_allowed_dash_context(
                        line_for_check, m.start(), m.end()
                    ):
                        continue
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
                if rule["id"].startswith(("AIGC", "PUNCT")):
                    continue
                for m in rule["_compiled"].finditer(line_for_check):
                    if rule["id"] == "PUNCT-002" and is_allowed_dash_context(
                        line_for_check, m.start(), m.end()
                    ):
                        continue
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
                for m in rule["_compiled"].finditer(line_for_check):
                    if target_format == "markdown":
                        if rule["id"] == "PUNCT-002" and is_markdown_table_separator(line):
                            continue
                        if rule["id"] == "AIGC-046" and is_markdown_structured_row(line):
                            continue
                    if target_format == "latex" and is_in_math_env(
                        line_for_check, m.start()
                    ):
                        continue  # 跳过行内数学环境
                    if rule["id"] == "PUNCT-002" and is_allowed_dash_context(
                        line_for_check, m.start(), m.end()
                    ):
                        continue
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

    # 连接词泛滥统计（仅当有连接词列表时）
    if connectives_words:
        connective_hits = []
        for i in range(start_line, end_line):
            line = lines[i]

            # 对 LaTeX 文件剥离行内注释
            if target_format == "latex":
                line_for_conn = mask_latex_inline_protected(strip_latex_comment(line))
            elif target_format == "markdown":
                line_for_conn = mask_inline_code(line)
            else:
                line_for_conn = line

            stripped = line_for_conn.lstrip()

            # 跳过整行注释（LaTeX）
            if target_format == "latex" and stripped.startswith("%"):
                continue
            if target_format == "markdown" and in_markdown_protected[i]:
                continue
            # 跳过块级数学和受保护环境
            if in_block_math[i] or in_protected_env[i]:
                continue

            for word in connectives_words:
                # 检查行首
                if stripped.startswith(word):
                    connective_hits.append(
                        {
                            "line": i + 1,
                            "column": 1,
                            "rule": "AIGC-CONN",
                            "severity": "info",
                            "message": f"段/句首连接词“{word}”（连接词泛滥检测）",
                            "fix": "评估是否可删除，目标削减 ≥ 50%",
                            "context": stripped[:60],
                        }
                    )
                # 检查句内句首（中文句号/问号/叹号后紧跟连接词）
                for sep in ("。", "！", "？"):
                    idx = stripped.find(sep + word)
                    if idx != -1:
                        col = len(line_for_conn) - len(stripped) + idx + len(sep) + 1
                        connective_hits.append(
                            {
                                "line": i + 1,
                                "column": col,
                                "rule": "AIGC-CONN",
                                "severity": "info",
                                "message": f"句首连接词“{word}”（连接词泛滥检测）",
                                "fix": "评估是否可删除，目标削减 ≥ 50%",
                                "context": stripped[:60],
                            }
                        )
        diagnostics.extend(connective_hits)

        # 去重：已被具体 AIGC 规则命中的词不再报 AIGC-CONN
        _aigc_flagged: set[tuple[int, str]] = set()
        for d in diagnostics:
            if d["rule"].startswith("AIGC-") and d["rule"] != "AIGC-CONN":
                for w in connectives_words:
                    if w in d["message"] or w in d.get("context", ""):
                        _aigc_flagged.add((d["line"], w))
        if _aigc_flagged:
            diagnostics = [
                d for d in diagnostics
                if d["rule"] != "AIGC-CONN" or not any(
                    d["line"] == line and w in d["message"]
                    for line, w in _aigc_flagged
                )
            ]

    # 突发性粗评（段落内句长方差）
    burstiness_warnings = check_burstiness(
        lines, start_line, end_line, target_format, in_protected_env
    )
    diagnostics.extend(burstiness_warnings)

    diagnostics.extend(
        check_quote_balance(
            lines, start_line, end_line, target_format, in_block_math, in_protected_env, in_markdown_protected
        )
    )
    diagnostics.extend(
        check_parentheses_policy(
            lines, start_line, end_line, target_format, in_block_math, in_protected_env, in_markdown_protected
        )
    )
    diagnostics.extend(
        check_fragmented_headers(
            lines, start_line, end_line, target_format, in_markdown_protected
        )
    )

    # 按行号排序
    diagnostics.sort(key=lambda d: (d["line"], d["column"]))

    # 三段式并列聚合统计
    diagnostics.extend(
        check_three_part_patterns(diagnostics, lines, start_line, end_line,
                                  target_format, in_block_math, in_protected_env, in_markdown_protected)
    )

    # 工程设计段落结构重复度聚合统计
    diagnostics.extend(
        check_module_enumeration_density(diagnostics, lines, start_line, end_line,
                                         target_format, in_block_math, in_protected_env, in_markdown_protected)
    )
    diagnostics.extend(
        check_clean_conclusion_density(diagnostics, lines, start_line, end_line,
                                       target_format, in_block_math, in_protected_env, in_markdown_protected)
    )
    diagnostics.extend(
        check_safety_jargon_density(diagnostics, lines, start_line, end_line,
                                    target_format, in_block_math, in_protected_env, in_markdown_protected)
    )
    diagnostics.extend(
        check_selection_template_density(diagnostics, lines, start_line, end_line,
                                         target_format, in_block_math, in_protected_env, in_markdown_protected)
    )

    return diagnostics


def check_burstiness(
    lines: list[str], start: int, end: int, target_format: str, in_protected_env=None
) -> list[dict]:
    warnings, para_start, para_sentences = [], None, []

    def _eval_para(p_start, sents):
        if len(sents) < 4:
            return None
        avg = sum(sents) / len(sents)
        variance = sum((s - avg) ** 2 for s in sents) / len(sents)
        # 方差过低 → 句长过于均匀 → 低突发性
        if avg > 0 and (variance**0.5) / avg < 0.20:
            return {
                "line": p_start + 1,
                "column": 1,
                "rule": "BURST-001",
                "severity": "info",
                "message": f"该段落句长方差过低（CV={((variance**0.5) / avg):.2f}），疑似低突发性",
                "fix": "插入极短句（3~5字）或超长参数句（20+字）以提升顿挫感",
                "context": f"段落起始行，含 {len(sents)} 句，平均句长 {avg:.0f} 字",
            }
        return None

    for i in range(start, end):
        # 如果在受保护环境内，跳过该行
        if (
            in_protected_env is not None
            and i < len(in_protected_env)
            and in_protected_env[i]
        ):
            continue

        line = lines[i].strip()
        # 空行或环境边界视为段落分隔
        if not line:
            if para_sentences:
                w = _eval_para(para_start, para_sentences)
                if w:
                    warnings.append(w)
            para_start = None
            para_sentences = []
            continue

        # LaTeX 特定分隔符
        if target_format == "latex":
            if line.startswith("\\section") or line.startswith("\\subsection"):
                if para_sentences:
                    w = _eval_para(para_start, para_sentences)
                    if w:
                        warnings.append(w)
                para_start = None
                para_sentences = []
                continue

        if (
            (target_format == "latex" and line.startswith("%"))
            or (target_format == "latex" and line.startswith("\\begin"))
            or (target_format == "latex" and line.startswith("\\end"))
        ):
            continue

        if para_start is None:
            para_start = i

        # 按中文句号/问号/叹号分句
        sentences = re.split(r"[。！？]", line)
        for s in sentences:
            # 移除 LaTeX 命令（仅 LaTeX）
            if target_format == "latex":
                clean = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", s)
            else:
                clean = s
            clean = re.sub(r"[^\u4e00-\u9fff]", "", clean)  # 只留中文字
            if len(clean) >= 2:
                para_sentences.append(len(clean))

    # 处理最后一个段落
    if para_sentences:
        w = _eval_para(para_start, para_sentences)
        if w:
            warnings.append(w)

    return warnings


def _is_allowed_parenthetical(content: str) -> bool:
    """判断括号内容是否属于必须保留的技术信息。"""
    value = content.strip()
    if not value:
        return False

    # 序号、缩写、变量名这类短标记不是解释性括号。
    if re.fullmatch(r"[0-9A-Za-z]+", value):
        return True

    has_chinese = re.search(r"[\u4e00-\u9fff]", value) is not None
    has_latin = re.search(r"[A-Za-z]", value) is not None
    has_digit = re.search(r"\d", value) is not None

    # 中文括号内容默认清理；专业解释需要化入正文。
    if has_chinese:
        return False

    # 英文全称、英文缩写、标准号、型号、参数单位等可保留。
    if has_latin:
        return True
    if has_digit and re.search(r"[%=+\-*/^~～·.,，\s]", value):
        return True

    return False


def check_parentheses_policy(
    lines: list[str],
    start: int,
    end: int,
    target_format: str,
    in_block_math: list[bool],
    in_protected_env: list[bool],
    in_markdown_protected: list[bool],
) -> list[dict]:
    """检测正文中不应保留的解释性括号。"""
    diagnostics = []
    paren_re = re.compile(r"[（(]([^（）()\n]{1,120})[）)]")

    for i in range(start, end):
        if in_block_math[i] or in_protected_env[i] or in_markdown_protected[i]:
            continue

        line = lines[i]
        if target_format == "latex":
            line_for_check = mask_latex_inline_protected(strip_latex_comment(line))
            if line_for_check.lstrip().startswith("%"):
                continue
        elif target_format == "markdown":
            line_for_check = mask_inline_code(line)
        else:
            line_for_check = line

        for m in paren_re.finditer(line_for_check):
            content = m.group(1)
            if _is_allowed_parenthetical(content):
                continue
            diagnostics.append(
                {
                    "line": i + 1,
                    "column": m.start() + 1,
                    "rule": "PUNCT-007",
                    "severity": "warning",
                    "message": "检测到正文解释性括号，当前规则下默认清理",
                    "fix": "只保留专业缩写、英文全称、标准号、型号和必要参数；中文解释括号应并入正文或删除",
                    "context": line.strip(),
                }
            )

    return diagnostics


def check_quote_balance(
    lines: list[str],
    start: int,
    end: int,
    target_format: str,
    in_block_math: list[bool],
    in_protected_env: list[bool],
    in_markdown_protected: list[bool],
) -> list[dict]:
    """检测中文弯引号是否成对出现。

    这类问题靠单个正则很难定位。按行检查虽不能覆盖跨段引用，但足够抓住
    常见的半边引号、误混英文引号和复制粘贴残留。
    """
    diagnostics = []
    pairs = [("“", "”", "PUNCT-005"), ("‘", "’", "PUNCT-006")]

    for i in range(start, end):
        if in_block_math[i] or in_protected_env[i] or in_markdown_protected[i]:
            continue

        line = lines[i]
        if target_format == "latex":
            line_for_check = mask_latex_inline_protected(strip_latex_comment(line))
            if line_for_check.lstrip().startswith("%"):
                continue
        elif target_format == "markdown":
            line_for_check = mask_inline_code(line)
        else:
            line_for_check = line

        for opener, closer, rule_id in pairs:
            if (line_for_check.count(opener) + line_for_check.count(closer)) % 2 == 1:
                first = min(
                    [pos for pos in (line_for_check.find(opener), line_for_check.find(closer)) if pos != -1],
                    default=0,
                )
                diagnostics.append(
                    {
                        "line": i + 1,
                        "column": first + 1,
                        "rule": rule_id,
                        "severity": "warning",
                        "message": f"检测到未成对的中文引号 {opener}{closer}",
                        "fix": "补齐引号或改为正确层级：外层“...”，内层‘...’；若只是强调词，直接删除引号",
                        "context": line.strip(),
                    }
                )

    return diagnostics


def check_fragmented_headers(
    lines: list[str],
    start: int,
    end: int,
    target_format: str,
    in_markdown_protected: list[bool],
) -> list[dict]:
    """检测标题后紧跟空话式重复说明的碎片化标题。"""
    diagnostics = []
    heading_re = re.compile(r"^\s{0,3}#{1,6}\s+|\\(?:sub)*section\*?\{")
    filler_re = re.compile(
        r"^(?:本(?:节|章|部分)|该部分|这一部分)(?:主要|将|旨在|用于|围绕|介绍|分析)"
        r"|^(?:性能|安全性|可靠性|精度|效率)(?:很|十分|非常)?(?:重要|关键)[。.]?$"
    )

    for i in range(start, end):
        if target_format == "markdown" and in_markdown_protected[i]:
            continue
        line = lines[i].strip()
        if not heading_re.search(line):
            continue

        j = i + 1
        while j < end and not lines[j].strip():
            j += 1
        if j >= end:
            continue
        if target_format == "markdown" and in_markdown_protected[j]:
            continue

        next_line = lines[j].strip()
        if target_format == "latex":
            next_line = strip_latex_comment(next_line).strip()
        if filler_re.search(next_line):
            diagnostics.append(
                {
                    "line": j + 1,
                    "column": 1,
                    "rule": "AIGC-064",
                    "severity": "info",
                    "message": "检测到标题后的空话式重复说明（碎片化标题）",
                    "fix": "让标题承担标题功能，正文直接写技术内容、参数、实验条件或结论",
                    "context": next_line[:80],
                }
            )

    return diagnostics


def check_three_part_patterns(
    diagnostics: list[dict],
    lines: list[str],
    start: int,
    end: int,
    target_format: str,
    in_block_math: list[bool],
    in_protected_env: list[bool],
    in_markdown_protected: list[bool],
) -> list[dict]:
    """聚合统计全文三段式并列结构密度，超过自适应阈值时产生告警。

    阈值：
    - 每 1000 字 > 2 处三段式 → warning
    - 每 1000 字 > 5 处三段式 → error
    """
    result = []

    # 统计 AIGC-046 命中次数
    three_part_hits = [d for d in diagnostics if d["rule"] == "AIGC-046"]

    if not three_part_hits:
        return result

    hit_count = len(three_part_hits)

    # 计算正文区域的汉字总数（跳过非正文行）
    chinese_char_count = 0
    for i in range(start, end):
        if in_block_math[i] or in_protected_env[i] or in_markdown_protected[i]:
            continue
        line = lines[i].strip()
        if target_format == "latex" and line.startswith("%"):
            continue
        chinese_char_count += sum(1 for c in line if "一" <= c <= "鿿")

    # 避免除零
    if chinese_char_count == 0:
        chinese_char_count = 1

    density = hit_count / (chinese_char_count / 1000)
    density_str = f"{density:.1f}"

    hit_lines = sorted({d["line"] for d in three_part_hits})

    if density > 5.0:
        result.append({
            "line": hit_lines[0] if hit_lines else start + 1,
            "column": 1,
            "rule": "AIGC-AGG-ERR",
            "severity": "error",
            "message": (
                f"全文三段式并列严重超标：{hit_count} 处 / {chinese_char_count} 字 "
                f"（密度 {density_str} 处/千字，阈值 5）。"
                f"AI 痕迹极强，须大幅削减。涉及行：{hit_lines}"
            ),
            "fix": "精选不超过 2 处/千字保留；其余强制改写为不同长度或不同结构的表达",
            "context": f"全文三段式密度 {density_str} 处/千字（error 阈值 5）",
        })
    elif density > 2.0:
        result.append({
            "line": hit_lines[0] if hit_lines else start + 1,
            "column": 1,
            "rule": "AIGC-AGG-WARN",
            "severity": "warning",
            "message": (
                f"全文三段式并列超标：{hit_count} 处 / {chinese_char_count} 字 "
                f"（密度 {density_str} 处/千字，阈值 2）。"
                f"需压缩至阈值以下。涉及行：{hit_lines}"
            ),
            "fix": "非技术术语枚举的三段式须调整项数或拆句；技术枚举融入段落",
            "context": f"全文三段式密度 {density_str} 处/千字（warning 阈值 2）",
        })

    return result


def _count_chinese_chars(
    lines: list[str],
    start: int,
    end: int,
    target_format: str,
    in_block_math: list[bool],
    in_protected_env: list[bool],
    in_markdown_protected: list[bool],
) -> int:
    """统计正文区域汉字总数（跳过非正文行）。"""
    count = 0
    for i in range(start, end):
        if in_block_math[i] or in_protected_env[i] or in_markdown_protected[i]:
            continue
        line = lines[i].strip()
        if target_format == "latex" and line.startswith("%"):
            continue
        count += sum(1 for c in line if "一" <= c <= "鿿")
    if count == 0:
        count = 1
    return count


def _build_agg_diagnostic(
    rule_id: str,
    severity: str,
    label: str,
    hit_count: int,
    chinese_char_count: int,
    threshold: int,
    hit_lines: list[int],
    fix: str,
) -> dict:
    """构建聚合诊断条目，格式与 check_three_part_patterns 输出一致。"""
    density = hit_count / (chinese_char_count / 1000)
    return {
        "line": hit_lines[0] if hit_lines else 1,
        "column": 1,
        "rule": rule_id,
        "severity": severity,
        "message": (
            f"全文{label}超标：{hit_count} 处 / {chinese_char_count} 字 "
            f"（密度 {density:.1f} 处/千字，阈值 {threshold}）。"
            f"涉及行：{hit_lines}"
        ),
        "fix": fix,
        "context": f"全文{label}密度 {density:.1f} 处/千字（阈值 {threshold}）",
    }


def check_module_enumeration_density(
    diagnostics: list[dict],
    lines: list[str],
    start: int,
    end: int,
    target_format: str,
    in_block_math: list[bool],
    in_protected_env: list[bool],
    in_markdown_protected: list[bool],
) -> list[dict]:
    """聚合统计功能模块流水账句式（AIGC-065），全章 > 3 处产生 warning。"""
    hits = [d for d in diagnostics if d["rule"] == "AIGC-065"]
    if len(hits) <= 3:
        return []
    chinese_char_count = _count_chinese_chars(
        lines, start, end, target_format, in_block_math, in_protected_env, in_markdown_protected
    )
    hit_lines = sorted({d["line"] for d in hits})
    return [_build_agg_diagnostic(
        "AIGC-AGG-MODULE", "warning", "功能模块流水账句式",
        len(hits), chinese_char_count, 3, hit_lines,
        "不要连续写模块A负责B；改为按工况、信号流或动作顺序说明部件为何承担该功能",
    )]


def check_clean_conclusion_density(
    diagnostics: list[dict],
    lines: list[str],
    start: int,
    end: int,
    target_format: str,
    in_block_math: list[bool],
    in_protected_env: list[bool],
    in_markdown_protected: list[bool],
) -> list[dict]:
    """聚合统计参数结论过圆（AIGC-068），全章 > 5 处产生 warning。"""
    hits = [d for d in diagnostics if d["rule"] == "AIGC-068"]
    if len(hits) <= 5:
        return []
    chinese_char_count = _count_chinese_chars(
        lines, start, end, target_format, in_block_math, in_protected_env, in_markdown_protected
    )
    hit_lines = sorted({d["line"] for d in hits})
    return [_build_agg_diagnostic(
        "AIGC-AGG-CONC", "warning", "参数结论过圆",
        len(hits), chinese_char_count, 5, hit_lines,
        "补出取值前提和边界条件；把三缸合力取写成三个缸的合力取，把该值高于计算载荷写成这个数值比前面算出来的载荷高了",
    )]


def check_safety_jargon_density(
    diagnostics: list[dict],
    lines: list[str],
    start: int,
    end: int,
    target_format: str,
    in_block_math: list[bool],
    in_protected_env: list[bool],
    in_markdown_protected: list[bool],
) -> list[dict]:
    """聚合统计安全规范口吻成串（AIGC-069），全章 > 5 处产生 warning。"""
    hits = [d for d in diagnostics if d["rule"] == "AIGC-069"]
    if len(hits) <= 5:
        return []
    chinese_char_count = _count_chinese_chars(
        lines, start, end, target_format, in_block_math, in_protected_env, in_markdown_protected
    )
    hit_lines = sorted({d["line"] for d in hits})
    return [_build_agg_diagnostic(
        "AIGC-AGG-SAFETY", "warning", "安全规范口吻成串",
        len(hits), chinese_char_count, 5, hit_lines,
        "把命令式(应/必须/禁止)改为联锁条件、传感器状态、阈值和故障后果；规范条文单独引用",
    )]


def check_selection_template_density(
    diagnostics: list[dict],
    lines: list[str],
    start: int,
    end: int,
    target_format: str,
    in_block_math: list[bool],
    in_protected_env: list[bool],
    in_markdown_protected: list[bool],
) -> list[dict]:
    """聚合统计选型模板复制（AIGC-070），全章 > 3 处产生 warning。"""
    hits = [d for d in diagnostics if d["rule"] == "AIGC-070"]
    if len(hits) <= 3:
        return []
    chinese_char_count = _count_chinese_chars(
        lines, start, end, target_format, in_block_math, in_protected_env, in_markdown_protected
    )
    hit_lines = sorted({d["line"] for d in hits})
    return [_build_agg_diagnostic(
        "AIGC-AGG-SELECT", "warning", "选型模板复制",
        len(hits), chinese_char_count, 3, hit_lines,
        "连续选用某方案 / 该方案模板必须轮换：改成这里选这个方案，主要是因为……",
    )]


# ── 输出格式化 ────────────────────────────────────────────



# ── 入口 ──────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="engineering-paper-humanizer 通用中文文本检测"
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
