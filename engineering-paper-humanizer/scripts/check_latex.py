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


# ── 规则定义 ──────────────────────────────────────────────

RULES = [
    # ── 引用格式 ──
    {
        "id": "CITE-001",
        "severity": "error",
        "pattern": r"。\s*\\cite\{",
        "message": "\\cite{} 出现在句号之后（应在句号内侧）",
        "fix": "将 \\cite{} 移到句号前：...\\cite{xxx}。",
    },
    {
        "id": "CITE-002",
        "severity": "error",
        "pattern": r"，\s*\\cite\{",
        "message": "\\cite{} 出现在逗号之后（应在逗号内侧）",
        "fix": "将 \\cite{} 移到逗号前：...\\cite{xxx}，",
    },
    {
        "id": "CITE-003",
        "severity": "error",
        "pattern": r"(?<=[^\s\\])\s+\\cite\{",
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
        "pattern": r"——",
        "message": "检测到中文破折号用于长解释（建议化入正文）",
        "fix": "将破折号解释内容改写为正文从句",
    },
    {
        "id": "PUNCT-003",
        "severity": "warning",
        "pattern": r"[）)]\s*[（(]",
        "message": "检测到连续括号堆砌",
        "fix": "合并括号内容或将解释化入正文",
    },
    # ── LaTeX 保护 ──
    {
        "id": "LATEX-001",
        "severity": "error",
        "pattern": r"(?<=\d)%(?!\s*$)",
        "message": "裸百分号 % 未转义（会导致行尾截断）",
        "fix": "改为 \\%",
    },
    {
        "id": "LATEX-002",
        "severity": "error",
        "pattern": r"\\(?:cite|label|ref|includegraphics)\{[^}]*\n",
        "message": "LaTeX 命令花括号内部存在换行",
        "fix": "将命令参数合并到同一行",
    },
    # ── AIGC 痕迹 ──
    {
        "id": "AIGC-001",
        "severity": "info",
        "pattern": r"本[章节]将(?:针对|详细|主要|重点)",
        "message": "检测到章节预告句式（AIGC 高频特征）",
        "fix": "删除预告，用客观主语自然过渡",
    },
    {
        "id": "AIGC-002",
        "severity": "info",
        "pattern": r"(?:具有|拥有)(?:十分|非常|极其)?重要的(?:工程|理论|实际|现实)(?:应用)?(?:价值|意义)",
        "message": "检测到空泛价值声明（AIGC 高频特征）",
        "fix": "删除或改为具体学术贡献描述",
    },
    {
        "id": "AIGC-003",
        "severity": "info",
        "pattern": r"(?:突破|攻克)了?.*?(?:技术瓶颈|关键难题)",
        "message": "检测到 AI 敏感词组\u201c突破技术瓶颈\u201d",
        "fix": "替换为\u201c克服...技术难点\u201d",
    },
    {
        "id": "AIGC-004",
        "severity": "info",
        "pattern": r"(?:提供|奠定)了?.*?(?:理论|数据|技术)(?:支撑|支持|基础)",
        "message": "检测到 AI 升华结尾\u201c提供数据支撑\u201d",
        "fix": "删除升华句，陈述完技术事实即结束段落",
    },
    {
        "id": "AIGC-005",
        "severity": "info",
        "pattern": r"(?:虽然|尽管).*?(?:取得了|已经|已有).*?(?:但是?|然而|不过).*?(?:仍然?|依然|尚)",
        "message": "检测到\u201c虽然...但仍...\u201d模板句（AIGC 高频模式）",
        "fix": "直接客观陈述双方侧重点",
    },
    {
        "id": "AIGC-006",
        "severity": "info",
        "pattern": r"应运而生",
        "message": "检测到 AI 敏感词\u201c应运而生\u201d",
        "fix": "直接删除",
    },
    {
        "id": "AIGC-007",
        "severity": "info",
        "pattern": r"双重困境",
        "message": "检测到 AI 敏感词\u201c双重困境\u201d",
        "fix": "替换为\u201c双重问题\u201d或\u201c局限性\u201d",
    },
    {
        "id": "AIGC-008",
        "severity": "info",
        "pattern": r"旨在(?:解决|探讨|研究)",
        "message": "检测到 AI 敏感词\u201c旨在解决/探讨\u201d",
        "fix": "替换为\u201c致力于改善\u201d或\u201c深入分析了\u201d",
    },
    # ── 模糊归因（新增） ──
    {
        "id": "AIGC-009",
        "severity": "info",
        "pattern": r"(?:行业报告|观察者|专家|一些批评者|多个来源)(?:显示|指出|认为|表明)",
        "message": "检测到模糊归因（应引用具体文献）",
        "fix": "替换为具体学者姓名+\\cite{xxx}引用",
    },
    # ── 协作交流残留（新增） ──
    {
        "id": "AIGC-010",
        "severity": "warning",
        "pattern": r"(?:希望这对您有帮助|请告诉我|您说得[完全]*正确|当然！|一定！)",
        "message": "检测到 AI 协作交流残留文本",
        "fix": "删除协作交流痕迹",
    },
    # ── 知识截止免责（新增） ──
    {
        "id": "AIGC-011",
        "severity": "warning",
        "pattern": r"(?:截至|根据我最后的|虽然具体细节有限|基于可用信息)",
        "message": "检测到 AI 知识截止免责声明残留",
        "fix": "删除免责声明，补充具体文献引用",
    },
    # ── 维度十四：否定式排比 ──
    {
        "id": "AIGC-012",
        "severity": "info",
        "pattern": r"(?:不仅仅是|这不仅仅是关于)",
        "message": "检测到否定式排比（AI 高频模式）",
        "fix": "删除否定式排比，直接陈述",
    },
    # ── 通用积极结论（新增） ──
    {
        "id": "AIGC-013",
        "severity": "info",
        "pattern": r"(?:未来看起来光明|激动人心的时代|追求卓越的旅程|向正确方向迈出)",
        "message": "检测到通用积极结论（AI 套话）",
        "fix": "删除套话，改为具体规划或直接删除",
    },
    # ── 过度限定（新增） ──
    {
        "id": "AIGC-014",
        "severity": "info",
        "pattern": r"可以潜在地(?:可能)?(?:被认为)?",
        "message": "检测到过度限定表达",
        "fix": "简化为直接陈述",
    },
    # ── 维度一：绝对化词汇 ──
    {
        "id": "AIGC-015",
        "severity": "info",
        "pattern": r"彻底解决",
        "message": "检测到绝对化词汇\u201c彻底解决\u201d",
        "fix": "降级为\u201c有效改善\u201d或\u201c显著降低\u201d",
    },
    # ── 维度六：文献综述起手式 ──
    {
        "id": "AIGC-016",
        "severity": "info",
        "pattern": r"(?:现有研究|已有研究|相关研究)(?:表明|显示|证明|指出)",
        "message": "检测到模糊文献综述起手式",
        "fix": "替换为具体学者引用（如\u201c张某等\\cite{xxx}指出\u201d）",
    },
    {
        "id": "AIGC-017",
        "severity": "info",
        "pattern": r"国内(?:外)?起步较晚",
        "message": "检测到 AI 文献综述套话\u201c国内起步较晚\u201d",
        "fix": "删除，直接陈述\u201c近年来，国内学者围绕XXX展开了针对性研究\u201d",
    },
    # ── 维度八：虚假权威 ──
    {
        "id": "AIGC-018",
        "severity": "info",
        "pattern": r"(?:众所周知|业内公认|普遍认为)",
        "message": "检测到虚假权威/模糊归因",
        "fix": "必须精确到具体参考文献编号或作者姓名",
    },
    {
        "id": "AIGC-019",
        "severity": "info",
        "pattern": r"(?:权威专家|大量实验)(?:建议|证明|表明)",
        "message": "检测到虚假权威声明",
        "fix": "删除或替换为具体实验数据+文献引用",
    },
    # ── 维度九：AI 对话口癖补充 ──
    {
        "id": "AIGC-020",
        "severity": "warning",
        "pattern": r"(?:让我们来看|好问题|正如您所指出|非常准确地描述)",
        "message": "检测到 AI 对话口癖残留",
        "fix": "彻底删除",
    },
    # ── 维度十：虚假范围词 ──
    {
        "id": "AIGC-021",
        "severity": "info",
        "pattern": r"(?:在某种程度上|在很大范围内|在一定程度上)",
        "message": "检测到虚假范围限定词",
        "fix": "删除或给出具体数值/工况区间",
    },
    # ── 维度十一：虚假-ing句式 ──
    {
        "id": "AIGC-022",
        "severity": "info",
        "pattern": r"(?:实现着|体现着|推动着|引领着|展现着)",
        "message": "检测到虚假\u201c着\u201d字深度句式（模仿英文-ing）",
        "fix": "改为直接动词陈述（\u201c实现了\u201d/\u201c体现了\u201d）",
    },
    # ── 维度十二：填充短语与过度限定 ──
    {
        "id": "AIGC-023",
        "severity": "info",
        "pattern": r"(?:可以说|基本上(?:可以)?说?)",
        "message": "检测到填充限定词",
        "fix": "删除，工程结论应当是确定性的",
    },
    {
        "id": "AIGC-024",
        "severity": "info",
        "pattern": r"具有广阔的(?:应用|发展)?前景",
        "message": "检测到通用积极结尾套话",
        "fix": "删除或改为具体技术规划",
    },
    # ── Part 2 困境/意图类补充 ──
    {
        "id": "AIGC-025",
        "severity": "info",
        "pattern": r"协同难题",
        "message": "检测到 AI 敏感词\u201c协同难题\u201d",
        "fix": "替换为\u201c协同障碍\u201d或\u201c控制挑战\u201d",
    },
    {
        "id": "AIGC-026",
        "severity": "info",
        "pattern": r"取得了一定(?:的)?进展",
        "message": "检测到 AI 模糊成果表述",
        "fix": "替换为具体科研动作（如\u201c提出了基于XX的算法\u201d）",
    },
    # ── Part 2 高频啰嗦副词 ──
    {
        "id": "AIGC-027",
        "severity": "info",
        "pattern": r"(?:从而实现|以期(?:实现|达到)?)",
        "message": "检测到 AI 高频啰嗦副词",
        "fix": "替换为\u201c以保证\u201d、\u201c迫使\u201d或\u201c以实现\u201d",
    },
    # ── Part 2 通用 AI 高频词 ──
    {
        "id": "AIGC-028",
        "severity": "info",
        "pattern": r"(?:至关重要|深入探讨|不可磨灭|充满活力)",
        "message": "检测到通用 AI 高频词",
        "fix": "按降重字典替换（至关重要→重要/关键，深入探讨→分析/研究）",
    },
    {
        "id": "AIGC-029",
        "severity": "info",
        "pattern": r"(?:不断演变|不断发展)的",
        "message": "检测到 AI 高频修饰语",
        "fix": "删除或改为具体变化描述",
    },
    # ── Part 2 填充短语 ──
    {
        "id": "AIGC-030",
        "severity": "info",
        "pattern": r"为了实现这一目标",
        "message": "检测到填充短语",
        "fix": "替换为\u201c为此\u201d",
    },
    {
        "id": "AIGC-031",
        "severity": "info",
        "pattern": r"(?:由于.*?的事实|在这个时间点|在.*?的情况下)",
        "message": "检测到冗余填充短语",
        "fix": "简化为\u201c因为\u201d/\u201c目前\u201d/\u201c若/当\u201d",
    },
    {
        "id": "AIGC-032",
        "severity": "info",
        "pattern": r"具有.*?的能力",
        "message": "检测到冗余能力表述",
        "fix": "简化为\u201c能够\u201d或\u201c可以\u201d",
    },
    # ── Part 2 模糊归因补充 ──
    {
        "id": "AIGC-033",
        "severity": "info",
        "pattern": r"研究人员(?:发现|认为|指出)",
        "message": "检测到模糊归因\u201c研究人员发现\u201d",
        "fix": "替换为具体学者姓名+\\cite{xxx}",
    },
    # ── Part 2 宣传/广告语言 ──
    {
        "id": "AIGC-034",
        "severity": "info",
        "pattern": r"(?:开创性的?|令人叹为观止|无缝(?:衔接|集成|体验|融合)|卓越性能|著名的|坐落于|充满活力的)",
        "message": "检测到宣传/广告语言",
        "fix": "替换为平实表述（开创性→新型的/改进的，无缝→删除）",
    },
    # ── 维度十二补充：过度限定词 ──
    {
        "id": "AIGC-035",
        "severity": "info",
        "pattern": r"似乎(?:可以|能够|表明)",
        "message": "检测到过度限定词\u201c似乎\u201d",
        "fix": "删除，工程结论应当是确定性的",
    },
    # ── Part 2 高频啰嗦副词补充 ──
    {
        "id": "AIGC-036",
        "severity": "info",
        "pattern": r"进一步加剧了这一状况",
        "message": "检测到 AI 高频啰嗦表述",
        "fix": "替换为\u201c使...进一步恶化\u201d",
    },
    # ── 粗体过度使用 ──
    {
        "id": "STYLE-001",
        "severity": "info",
        "pattern": r"(?:\*\*[^*]{2,}\*\*.*){3}|(?:\\textbf\{[^}]+\}.*){3}",
        "message": "检测到单行内多处粗体标记（可能为 AI 过度强调）",
        "fix": "减少粗体使用，仅在首次定义术语时使用",
    },
    # ── 维度十三：避免使用"是"（系动词回避） ──
    {
        "id": "AIGC-037",
        "severity": "info",
        "pattern": r"(?:作为|代表|标志着|充当)了?(?:一个|一种)?(?:提升|关键|体现|证明)",
        "message": "检测到系动词回避（AI 喜欢用复杂结构替代简单的系动词）",
        "fix": "改为简单的动词陈述（如\u201c提升了\u201d）",
    },
    # ── 维度十五：消除"提纲式挑战"部分 ──
    {
        "id": "AIGC-038",
        "severity": "info",
        "pattern": r"(?:面临若干挑战|挑战与遗产|尽管存在这些挑战)",
        "message": "检测到提纲式挑战声明（AI 模板句）",
        "fix": "直接陈述具体的技术瓶颈",
    },
    # ── 表情符号（新增） ──
    {
        "id": "STYLE-002",
        "severity": "warning",
        "pattern": r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\u2702-\u27B0\u2600-\u26FF\u2700-\u27BF\u231A\u231B\u23E9-\u23F3\u23F8-\u23FA\u25AA\u25AB\u25B6\u25C0\u25FB-\u25FE]",
        "message": "检测到表情符号（学术论文中不应使用）",
        "fix": "删除表情符号",
    },
]

# 连接词泛滥检测（独立统计）
CONNECTIVES = [
    "因此",
    "然而",
    "值得注意的是",
    "此外",
    "与此同时",
    "综上所述",
    "由此可见",
    "不仅如此",
    "更重要的是",
    "总而言之",
    "总的来说",
    "换言之",
    "事实上",
    "显而易见",
    "不可否认",
    "毫无疑问",
    "众所周知",
    "正如前文所述",
    "如前所述",
    "接下来",
]


# ── 核心逻辑 ────────────────────────────────────────���─────


def is_in_math_env(line: str, match_start: int) -> bool:
    """粗略判断匹配位置是否处于行内数学环境 $ $ 内部"""
    dollars = [m.start() for m in re.finditer(r"(?<!\\)\$", line)]
    depth = 0
    for d in dollars:
        if d >= match_start:
            break
        depth += 1
    return depth % 2 == 1


def precompute_block_math(lines: list[str]) -> list[bool]:
    """预计算每一行是否处于块级数学环境内（O(n) 单次遍历）"""
    math_envs = (
        "equation",
        "align",
        "gather",
        "multline",
        "eqnarray",
        "math",
        "displaymath",
    )
    depth = 0
    result = []
    for line in lines:
        for env in math_envs:
            depth += len(re.findall(rf"\\begin\{{{env}\*?\}}", line))
            depth -= len(re.findall(rf"\\end\{{{env}\*?\}}", line))
        result.append(depth > 0)
    return result


def check_file(filepath: str, section: int | None = None) -> list[dict]:
    """执行全部检查规则，返回诊断列表"""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_block_math = precompute_block_math(lines)

    # 如果指定了 section，定位范围
    start_line, end_line = 0, len(lines)
    if section is not None:
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

    diagnostics = []

    # 逐行规则匹配
    for i in range(start_line, end_line):
        line = lines[i]

        # 跳过注释行
        stripped = line.lstrip()
        if stripped.startswith("%"):
            continue

        # 跳过块级数学环境
        if in_block_math[i]:
            # 只跳过 AIGC/PUNCT 类规则，CITE/LATEX 规则仍然检查
            for rule in RULES:
                if rule["id"].startswith(("AIGC", "PUNCT")):
                    continue
                for m in re.finditer(rule["pattern"], line):
                    if not is_in_math_env(line, m.start()):
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
            for rule in RULES:
                for m in re.finditer(rule["pattern"], line):
                    if not is_in_math_env(line, m.start()):
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

    # 连接词泛滥统计
    connective_hits = []
    for i in range(start_line, end_line):
        line = lines[i]
        stripped = line.lstrip()
        if stripped.startswith("%"):
            continue
        if in_block_math[i]:
            continue
        for word in CONNECTIVES:
            if stripped.startswith(word):
                connective_hits.append(
                    {
                        "line": i + 1,
                        "column": 1,
                        "rule": "AIGC-CONN",
                        "severity": "info",
                        "message": f"段/句首连接词\u201c{word}\u201d（连接词泛滥检测）",
                        "fix": "评估是否可删除，目标削减 ≥ 50%",
                        "context": stripped[:60],
                    }
                )

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
        if avg > 0 and (variance**0.5) / avg < 0.25:
            return {
                "line": p_start + 1,
                "column": 1,
                "rule": "BURST-001",
                "severity": "warning",
                "message": f"该段落句长方差过低（CV={((variance**0.5) / avg):.2f}），疑似低突发性",
                "fix": "插入极短句（3~5字）或超长参数句（20+字）以提升顿挫感",
                "context": f"段落起始行，含 {len(sents)} 句，平均句长 {avg:.0f} 字",
            }
        return None

    for i in range(start, end):
        line = lines[i].strip()
        # 空行或环境边界视为段落分隔
        if not line or line.startswith("\\section") or line.startswith("\\subsection"):
            if para_sentences:
                w = _eval_para(para_start, para_sentences)
                if w:
                    warnings.append(w)
            para_start = None
            para_sentences = []
            continue

        if (
            line.startswith("%")
            or line.startswith("\\begin")
            or line.startswith("\\end")
        ):
            continue

        if para_start is None:
            para_start = i

        # 按中文句号/问号/叹号分句
        sentences = re.split(r"[。！？]", line)
        for s in sentences:
            clean = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", s)  # 移除 LaTeX 命令
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

    counts = {"error": 0, "warning": 0, "info": 0}
    lines = []
    lines.append(f"{'=' * 60}")
    lines.append(f"  检查文件: {filepath}")
    lines.append(f"{'=' * 60}")

    for d in diagnostics:
        counts[d["severity"]] += 1
        icon = SEVERITY_ICONS[d["severity"]]
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
        description="engineering-paper-humanizer LaTeX 格式检查"
    )
    parser.add_argument("file", help="要检查的 .tex 文件路径")
    parser.add_argument(
        "--section",
        type=int,
        default=None,
        help="只检查指定章节编号（按 \\section 出现顺序从 1 计数）",
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
