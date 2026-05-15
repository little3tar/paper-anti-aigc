#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 format_rules.json 生成人类可读的格式规则速查表

生成 Markdown 格式的格式规则速查表，可用于文档或快速参考。
不用于实际检测，仅用于人类阅读。

用法:
    python scripts/generate_format_dict.py > format-dict.md
    python scripts/generate_format_dict.py --format latex > format-dict-latex.md
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

from _shared import setup_windows_utf8, generate_rule_dict_markdown

setup_windows_utf8()

CONFIG = {
    "rules_path": str(Path(__file__).parent / "format_rules.json"),
    "title": "# 学术文档格式规则速查表（自动生成）",
    "script_name": "generate_format_dict.py",
    "check_script": "check_format.py",
    "header_left": "❌ 格式模式/问题",
    "header_right": "✅ 修复方式",
    "always_show_connectives": False,
    "output_filename": "format-dict.md",
}


def main():
    parser = argparse.ArgumentParser(description="从 format_rules.json 生成格式规则速查表")
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

    markdown = generate_rule_dict_markdown(**CONFIG, format_filter=args.format)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"[OK] 已生成: {output_path}", file=sys.stderr)
    else:
        print(markdown)


if __name__ == "__main__":
    main()
