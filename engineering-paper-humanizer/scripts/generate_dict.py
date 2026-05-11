#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 rules.json 生成人类可读的敏感词速查表

生成 Markdown 格式的敏感词替换字典，可用于文档或快速参考。
不用于实际检测，仅用于人类阅读。

用法:
    python3 scripts/generate_dict.py > dict.md
    python3 scripts/generate_dict.py --format latex > dict-latex.md
"""

from __future__ import annotations

import sys
import io
import os
import re
import json
from pathlib import Path

# ── Windows GBK 兼容：强制 stdout/stderr 使用 UTF-8 ────────
if os.name == "nt":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def load_rules() -> tuple[list[dict], dict]:
    """从 rules.json 加载规则和连接词"""
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

    return data.get("rules", []), data.get("connectives", {})


def categorize_rules(rules: list[dict]) -> dict[str, list[dict]]:
    """按规则 ID 前缀分组（与 rules.json 保持一致，无硬编码）"""
    # ID 前缀 → 人类可读分类名
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


def format_markdown_table(rules: list[dict]) -> str:
    """生成 Markdown 表格"""
    if not rules:
        return ""

    lines = []
    lines.append("| ❌ AI 高频词/短语 | ✅ 替换为 | 严重程度 | 适用格式 |")
    lines.append("|-------------------|-----------|----------|----------|")

    for rule in rules:
        # 提取敏感词（从 pattern 中提取人类可读部分）
        pattern = rule.get("pattern", "")
        message = rule.get("message", "")

        # 简化 pattern 显示
        display_pattern = pattern
        if len(pattern) > 40:
            display_pattern = pattern[:37] + "..."

        # 清理正则元字符
        display_pattern = display_pattern.replace("\\", "")
        display_pattern = display_pattern.replace("(?:", "")
        display_pattern = display_pattern.replace(")", "")
        display_pattern = display_pattern.replace(".*?", "…")
        display_pattern = display_pattern.replace("?", "")
        display_pattern = display_pattern.replace("*", "")
        display_pattern = display_pattern.replace("+", "")
        display_pattern = display_pattern.replace("[", "")
        display_pattern = display_pattern.replace("]", "")
        display_pattern = display_pattern.replace("^", "")
        display_pattern = display_pattern.replace("$", "")
        display_pattern = display_pattern.replace("|", " 或 ")

        # 提取替换建议
        fix = rule.get("fix", "")
        if "替换为" in message:
            # 从 message 提取替换词
            match = re.search(r"替换为[「\"']?([^」\"']+)[」\"']?", message)
            if match:
                fix = match.group(1)

        # 严重程度图标
        severity = rule.get("severity", "info")
        severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(
            severity, "⚪"
        )

        # 适用格式
        formats = rule.get("format", ["latex"])
        format_str = ", ".join(formats)

        lines.append(
            f"| `{display_pattern}` | {fix} | {severity_icon} {severity} | {format_str} |"
        )

    return "\n".join(lines)


def generate_markdown(format_filter: str = "all") -> str:
    """生成完整的 Markdown 文档"""
    rules, connectives = load_rules()
    categories = categorize_rules(rules)

    lines = []
    lines.append("# AI 敏感词替换字典（自动生成）")
    lines.append("")
    lines.append("> 本文件由 `scripts/generate_dict.py` 从 `rules.json` 自动生成。")
    lines.append("> 实际检测请使用 `python3 scripts/check_aigc.py <file>`。")
    lines.append("")
    lines.append("## 连接词泛滥检测")
    lines.append("")
    lines.append("以下连接词在段/句首出现时，建议删除至少 50%：")
    lines.append("")

    # 连接词列表
    if connectives and "words" in connectives:
        words = connectives["words"]
        lines.append("```")
        for i in range(0, len(words), 8):
            lines.append("  " + "  ".join(words[i : i + 8]))
        lines.append("```")
        lines.append("")

    # 各分类表格
    for cat_name, cat_rules in categories.items():
        if not cat_rules:
            continue

        lines.append(f"## {cat_name}")
        lines.append("")

        # 按格式过滤
        if format_filter != "all":
            filtered_rules = [
                r for r in cat_rules if format_filter in r.get("format", ["latex"])
            ]
            if not filtered_rules:
                continue
            lines.append(f"*（仅显示 {format_filter} 格式相关规则）*")
            lines.append("")
            lines.append(format_markdown_table(filtered_rules))
        else:
            lines.append(format_markdown_table(cat_rules))

        lines.append("")

    # 使用说明
    lines.append("## 使用说明")
    lines.append("")
    lines.append("1. **实际检测**：运行 `python3 scripts/check_aigc.py <file>`")
    lines.append("2. **格式支持**：")
    lines.append("   - LaTeX: `python3 scripts/check_aigc.py paper.tex`")
    lines.append(
        "   - Markdown: `python3 scripts/check_aigc.py paper.md --format markdown`"
    )
    lines.append(
        "   - 纯文本: `python3 scripts/check_aigc.py draft.txt --format plain`"
    )
    lines.append("3. **重新生成本文件**：`python3 scripts/generate_dict.py > dict.md`")
    lines.append("")
    lines.append("---")
    lines.append("*生成时间：自动生成，请勿手动编辑*")

    return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="从 rules.json 生成敏感词速查表")
    parser.add_argument(
        "--format",
        choices=["all", "latex", "markdown", "plain"],
        default="all",
        help="过滤规则格式（默认: all）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出文件路径（默认: stdout）",
    )
    args = parser.parse_args()

    markdown = generate_markdown(args.format)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"[OK] 已生成: {output_path}", file=sys.stderr)
    else:
        print(markdown)


if __name__ == "__main__":
    main()
