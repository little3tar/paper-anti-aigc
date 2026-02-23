#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""engineering-paper-humanizer LaTeX 格式检查脚本

扫描 .tex 文件，检测常见的 AIGC 残留格式问题和 LaTeX 规范违规。
输出结构化的逐行诊断结果，供 agent 或人工快速定位修复。

用法:
    python3 scripts/check_latex.py <file.tex>
    python3 scripts/check_latex.py <file.tex> --section 3
    python3 scripts/check_latex.py <file.tex> --json
"""

import re
import sys
import json
import argparse
from pathlib import Path

# ── Windows GBK 兼容：强制 stdout/stderr 使用 UTF-8 ────────
import io, os
if os.name == 'nt':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ── 规则定义 ──────────────────────────────────────────────

RULES = [
    # ── 引用格式 ──
    # ── 在 RULES 列表末尾、最后一个 } 之后追加 ──
    # {
    #     "id": "AIGC-009",           # 规则 ID，按类别编号递增
    #     "severity": "info",         # error / warning / info 三选一
    #     "pattern": r'从而实现',      # Python 正则表达式
    #     "message": "检测到 AI 敏感词"从而实现"",
    #     "fix": "替换为"以保证"或"迫使"",
    # },
    {
        "id": "CITE-001",
        "severity": "error",
        "pattern": r'。\s*\\cite\{',
        "message": "\\cite{} 出现在句号之后（应在句号内侧）",
        "fix": "将 \\cite{} 移到句号前：...\\cite{xxx}。",
    },
    {
        "id": "CITE-002",
        "severity": "error",
        "pattern": r'，\s*\\cite\{',
        "message": "\\cite{} 出现在逗号之后（应在逗号内侧）",
        "fix": "将 \\cite{} 移到逗号前：...\\cite{xxx}，",
    },
    {
        "id": "CITE-003",
        "severity": "error",
        "pattern": r'(?<=[^\s\\])\s+\\cite\{',
        "message": "\\cite{} 前存在空格",
        "fix": "删除 \\cite{} 前的空格，使其紧贴被引文字",
    },
    # ── 标点规范 ──
    {
        "id": "PUNCT-001",
        "severity": "warning",
        "pattern": r'(?<![\\])"[^"]*"',
        "message": "检测到英文双引号，中文论文应使用 \u201c \u201d",
        "fix": "替换为中文双引号 \\u201c \\u201d",
    },
    {
        "id": "PUNCT-002",
        "severity": "warning",
        "pattern": r'——',
        "message": "检测到中文破折号用于长解释（建议化入正文）",
        "fix": "将破折号解释内容改写为正文从句",
    },
    {
        "id": "PUNCT-003",
        "severity": "warning",
        "pattern": r'[）)]\s*[（(]',
        "message": "检测到连续括号堆砌",
        "fix": "合并括号内容或将解释化入正文",
    },
    # ── LaTeX 保护 ──
    {
        "id": "LATEX-001",
        "severity": "error",
        "pattern": r'(?<=\d)%(?!\s*$)',
        "message": "裸百分号 % 未转义（会导致行尾截断）",
        "fix": "改为 \\%",
    },
    {
        "id": "LATEX-002",
        "severity": "error",
        "pattern": r'\\(?:cite|label|ref|includegraphics)\{[^}]*\n',
        "message": "LaTeX 命令花括号内部存在换行",
        "fix": "将命令参数合并到同一行",
    },
    # ── AIGC 痕迹 ──
    {
        "id": "AIGC-001",
        "severity": "info",
        "pattern": r'本[章节]将(?:针对|详细|主要|重点)',
        "message": "检测到章节预告句式（AIGC 高频特征）",
        "fix": "删除预告，用客观主语自然过渡",
    },
    {
        "id": "AIGC-002",
        "severity": "info",
        "pattern": r'(?:具有|拥有)(?:十分|非常|极其)?重要的(?:工程|理论|实际|现实)(?:应用)?(?:价值|意义)',
        "message": "检测到空泛价值声明（AIGC 高频特征）",
        "fix": "删除或改为具体学术贡献描述",
    },
    {
        "id": "AIGC-003",
        "severity": "info",
        "pattern": r'(?:突破|攻克)了?.*?(?:技术瓶颈|关键难题)',
        "message": "检测到 AI 敏感词组\u201c突破技术瓶颈\u201d",
        "fix": "替换为\u201c克服...技术难点\u201d",
    },
    {
        "id": "AIGC-004",
        "severity": "info",
        "pattern": r'(?:提供|奠定)了?.*?(?:理论|数据|技术)(?:支撑|支持|基础)',
        "message": "检测到 AI 升华结尾\u201c提供数据支撑\u201d",
        "fix": "删除升华句，陈述完技术事实即结束段落",
    },
    {
        "id": "AIGC-005",
        "severity": "info",
        "pattern": r'(?:虽然|尽管).*?(?:取得了|已经|已有).*?(?:但是?|然而|不过).*?(?:仍然?|依然|尚)',
        "message": "检测到\u201c虽然...但仍...\u201d模板句（AIGC 高频模式）",
        "fix": "直接客观陈述双方侧重点",
    },
    {
        "id": "AIGC-006",
        "severity": "info",
        "pattern": r'应运而生',
        "message": "检测到 AI 敏感词\u201c应运而生\u201d",
        "fix": "直接删除",
    },
    {
        "id": "AIGC-007",
        "severity": "info",
        "pattern": r'双重困境',
        "message": "检测到 AI 敏感词\u201c双重困境\u201d",
        "fix": "替换为\u201c双重问题\u201d或\u201c局限性\u201d",
    },
    {
        "id": "AIGC-008",
        "severity": "info",
        "pattern": r'旨在(?:解决|探讨|研究)',
        "message": "检测到 AI 敏感词\u201c旨在解决/探讨\u201d",
        "fix": "替换为\u201c致力于改善\u201d或\u201c深入分析了\u201d",
    },
]

# 连接词泛滥检测（独立统计）
CONNECTIVES = [
    '因此', '然而', '值得注意的是', '此外', '与此同时',
    '综上所述', '由此可见', '不仅如此', '更重要的是',
    '总而言之', '换言之', '事实上', '显而易见',
]


# ── 核心逻辑 ────────────────────────────────────────���─────

def is_in_math_env(line: str, match_start: int) -> bool:
    """粗略判断匹配位置是否处于行内数学环境 $ $ 内部"""
    dollars = [m.start() for m in re.finditer(r'(?<!\\)\$', line)]
    depth = 0
    for d in dollars:
        if d >= match_start:
            break
        depth += 1
    return depth % 2 == 1


def is_in_block_math(lines: list[str], line_idx: int) -> bool:
    """判断当前行是否处于 equation/align 等块级数学环境内"""
    depth = 0
    math_envs = ('equation', 'align', 'gather', 'multline', 'eqnarray', 'math', 'displaymath')
    for i in range(line_idx + 1):
        for env in math_envs:
            depth += len(re.findall(rf'\\begin\{{{env}\*?\}}', lines[i]))
            depth -= len(re.findall(rf'\\end\{{{env}\*?\}}', lines[i]))
    return depth > 0


def check_file(filepath: str, section: int | None = None) -> list[dict]:
    """执行全部检查规则，返回诊断列表"""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()

    # 如果指定了 section，定位范围
    start_line, end_line = 0, len(lines)
    if section is not None:
        sec_pattern = re.compile(rf'\\section\b')
        sec_positions = []
        for i, line in enumerate(lines):
            if sec_pattern.search(line):
                sec_positions.append(i)
        if section - 1 < len(sec_positions):
            start_line = sec_positions[section - 1]
            end_line = sec_positions[section] if section < len(sec_positions) else len(lines)

    diagnostics = []

    # 逐行规则匹配
    for i in range(start_line, end_line):
        line = lines[i]

        # 跳过注释行
        stripped = line.lstrip()
        if stripped.startswith('%'):
            continue

        # 跳过块级数学环境
        if is_in_block_math(lines, i):
            # 只跳过 AIGC/PUNCT 类规则，CITE/LATEX 规则仍然检查
            for rule in RULES:
                if rule["id"].startswith(("AIGC", "PUNCT")):
                    continue
                for m in re.finditer(rule["pattern"], line):
                    if not is_in_math_env(line, m.start()):
                        diagnostics.append({
                            "line": i + 1,
                            "column": m.start() + 1,
                            "rule": rule["id"],
                            "severity": rule["severity"],
                            "message": rule["message"],
                            "fix": rule["fix"],
                            "context": line.strip(),
                        })
        else:
            for rule in RULES:
                for m in re.finditer(rule["pattern"], line):
                    if not is_in_math_env(line, m.start()):
                        diagnostics.append({
                            "line": i + 1,
                            "column": m.start() + 1,
                            "rule": rule["id"],
                            "severity": rule["severity"],
                            "message": rule["message"],
                            "fix": rule["fix"],
                            "context": line.strip(),
                        })

    # 连接词泛滥统计
    connective_hits = []
    for i in range(start_line, end_line):
        line = lines[i]
        stripped = line.lstrip()
        if stripped.startswith('%'):
            continue
        if is_in_block_math(lines, i):
            continue
        for word in CONNECTIVES:
            if stripped.startswith(word):
                connective_hits.append({
                    "line": i + 1,
                    "column": 1,
                    "rule": "AIGC-CONN",
                    "severity": "info",
                    "message": f"段/句首连接词\u201c{word}\u201d（连接词泛滥检测）",
                    "fix": "评估是否可删除，目标削减 ≥ 50%",
                    "context": stripped[:60],
                })

    diagnostics.extend(connective_hits)

    # 突发性粗评（段落内句长方差）
    burstiness_warnings = check_burstiness(lines, start_line, end_line)
    diagnostics.extend(burstiness_warnings)

    # 按行号排序
    diagnostics.sort(key=lambda d: (d["line"], d["column"]))
    return diagnostics


def check_burstiness(lines: list[str], start: int, end: int) -> list[dict]:
    """粗略评估段落内句子长度的突发性（方差）"""
    warnings = []
    para_start = None
    para_sentences: list[int] = []

    def _eval_para(p_start, sents):
        if len(sents) < 4:
            return None
        avg = sum(sents) / len(sents)
        variance = sum((s - avg) ** 2 for s in sents) / len(sents)
        # 方差过低 → 句长过于均匀 → 低突发性
        if avg > 0 and (variance ** 0.5) / avg < 0.25:
            return {
                "line": p_start + 1,
                "column": 1,
                "rule": "BURST-001",
                "severity": "warning",
                "message": f"该段落句长方差过低（CV={((variance**0.5)/avg):.2f}），疑似低突发性",
                "fix": "插入极短句（3~5字）或超长参数句（20+字）以提升顿挫感",
                "context": f"段落起始行，含 {len(sents)} 句，平均句长 {avg:.0f} 字",
            }
        return None

    for i in range(start, end):
        line = lines[i].strip()
        # 空行或环境边界视为段落分隔
        if not line or line.startswith('\\section') or line.startswith('\\subsection'):
            if para_sentences:
                w = _eval_para(para_start, para_sentences)
                if w:
                    warnings.append(w)
            para_start = None
            para_sentences = []
            continue

        if line.startswith('%') or line.startswith('\\begin') or line.startswith('\\end'):
            continue

        if para_start is None:
            para_start = i

        # 按中文句号/问号/叹号分句
        sentences = re.split(r'[。！？]', line)
        for s in sentences:
            clean = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', s)  # 移除 LaTeX 命令
            clean = re.sub(r'[^\u4e00-\u9fff]', '', clean)   # 只留中文字
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

    counts = {"error": 0, "warning": 0, "info": 0}
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"  检查文件: {filepath}")
    lines.append(f"{'='*60}")

    for d in diagnostics:
        counts[d["severity"]] += 1
        icon = SEVERITY_ICONS[d["severity"]]
        lines.append(f"")
        lines.append(f"{icon} [{d['rule']}] L{d['line']}:{d['column']}  {d['message']}")
        lines.append(f"   上下文: {d['context'][:80]}")
        lines.append(f"   修复建议: {d['fix']}")

    lines.append(f"")
    lines.append(f"{'='*60}")
    lines.append(f"  汇总: {counts['error']} 错误 | {counts['warning']} 警告 | {counts['info']} 提示")
    lines.append(f"{'='*60}")

    return "\n".join(lines)


# ── 入口 ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="engineering-paper-humanizer LaTeX 格式检查"
    )
    parser.add_argument("file", help="要检查的 .tex 文件路径")
    parser.add_argument(
        "--section", type=int, default=None,
        help="只检查指定章节编号（按 \\section 出现顺序从 1 计数）"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="输出 JSON 格式（供 agent 解析）"
    )
    parser.add_argument(
        "--severity", default=None, choices=["error", "warning", "info"],
        help="只显示指定严重级别及以上"
    )
    args = parser.parse_args()

    diagnostics = check_file(args.file, args.section)

    # 过滤严重级别
    if args.severity:
        levels = {"error": 3, "warning": 2, "info": 1}
        threshold = levels[args.severity]
        diagnostics = [d for d in diagnostics if levels[d["severity"]] >= threshold]

    if args.json:
        print(json.dumps(diagnostics, ensure_ascii=False, indent=2))
    else:
        print(format_text(diagnostics, args.file))


if __name__ == "__main__":
    main()