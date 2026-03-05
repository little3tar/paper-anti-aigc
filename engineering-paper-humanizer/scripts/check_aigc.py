#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""engineering-paper-humanizer AIGC 检测脚本

扫描 LaTeX (.tex)、Markdown (.md) 或纯文本文件，检测 AIGC 残留格式问题和规范违规。
输出结构化的逐行诊断结果，供 agent 或人工快速定位修复。

用法:
    python3 scripts/check_aigc.py <file.tex>                    # LaTeX 文件（默认）
    python3 scripts/check_aigc.py <file.md> --format markdown   # Markdown 文件
    python3 scripts/check_aigc.py <file.txt> --format plain     # 纯文本文件
    python3 scripts/check_aigc.py <file.tex> --section 3        # 只检查指定章节
    python3 scripts/check_aigc.py <file.tex> --json             # JSON 格式输出
    python3 scripts/check_aigc.py <file.tex> --severity error   # 只显示错误
"""

from __future__ import annotations

import re
import sys
import json
import argparse
from pathlib import Path

# ── Windows GBK 兼容：强制 stdout/stderr 使用 UTF-8 ────────
import io, os

if os.name == "nt":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── 从 rules.json 加载规则 ──────────────────────────────────


def load_rules(format_filter: str = "latex") -> tuple[list[dict], list[str]]:
    """从 rules.json 加载规则和连接词，按 format 过滤

    参数:
        format_filter: "latex" | "markdown" | "plain"

    返回:
        (rules, connectives_words)
    """
    script_dir = Path(__file__).parent
    rules_path = script_dir / "rules.json"

    if not rules_path.exists():
        print(f"[ERROR] 规则文件不存在: {rules_path}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(rules_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] 无法加载 rules.json: {e}", file=sys.stderr)
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
    """预计算每一行是否处于受保护的 LaTeX 环境内（tikzpicture, table, figure）

    这些环境内的 AIGC/PUNCT/STYLE 规则应被跳过（仅检查 CITE/LATEX）。
    """
    protected_envs = ("tikzpicture", "table", "figure")
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

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # 加载规则（按 format 过滤）
    rules, connectives_words = load_rules(target_format)

    # 预编译正则表达式（避免每行重复编译）
    for rule in rules:
        rule["_compiled"] = re.compile(rule["pattern"])

    # 数学环境检测（仅 LaTeX）
    if target_format == "latex":
        in_block_math = precompute_block_math(lines)
        # 受保护环境检测（tikzpicture, table, figure）
        in_protected_env = precompute_protected_envs(lines)
    else:
        in_block_math = [False] * len(lines)
        in_protected_env = [False] * len(lines)

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

        # 对 LaTeX 文件剥离行内注释
        if target_format == "latex":
            line_for_check = strip_latex_comment(line)
        else:
            line_for_check = line

        # 检查是否在受保护环境内（tikzpicture/table/figure）
        if target_format == "latex" and in_protected_env[i]:
            # 受保护环境内：跳过 AIGC/PUNCT/STYLE 规则，只检查 CITE/LATEX 规则
            for rule in rules:
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

    # 连接词泛滥统计（仅当有连接词列表时）
    if connectives_words:
        connective_hits = []
        for i in range(start_line, end_line):
            line = lines[i]

            # 对 LaTeX 文件剥离行内注释
            if target_format == "latex":
                line_for_conn = strip_latex_comment(line)
            else:
                line_for_conn = line

            stripped = line_for_conn.lstrip()

            # 跳过整行注释（LaTeX）
            if target_format == "latex" and stripped.startswith("%"):
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

    # 突发性粗评（段落内句长方差）
    burstiness_warnings = check_burstiness(
        lines, start_line, end_line, target_format, in_protected_env
    )
    diagnostics.extend(burstiness_warnings)

    # 按行号排序
    diagnostics.sort(key=lambda d: (d["line"], d["column"]))
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


# ── 输出格式化 ────────────────────────────────────────────

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


# ── 入口 ──────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="engineering-paper-humanizer AIGC 检测"
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
