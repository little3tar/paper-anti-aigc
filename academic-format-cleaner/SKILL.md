---
name: academic-format-cleaner
description: 检查和修复学术文档的格式层问题，适用于 LaTeX、Markdown 和纯文本草稿中的引用位置、LaTeX 命令、百分号转义、命令参数断行、列表格式、代码/数学环境保护等。用户提到论文格式检查、LaTeX 报错、引用位置、Markdown/tex/txt 格式规范、公式或命令被润色误伤时，应使用此 skill；不要用于正文去 AI 化，正文润色交给 engineering-paper-humanizer。
---

# Academic Format Cleaner

本 skill 只处理格式层问题，不负责改写正文风格。它与 `engineering-paper-humanizer` 分工如下：

运行脚本需要 Python 3.7 或更高版本。

- `engineering-paper-humanizer`：中文工程论文正文、AI 腔、通用中文标点、引号、破折号。
- `academic-format-cleaner`：LaTeX/Markdown/plain 的格式约束、引用位置、命令保护、结构性格式问题。

## Position In Thesis Workflow

在完整论文写作流程中，本 skill 应作为最后一道后处理使用。

推荐顺序：

1. `thesis-outline-planner`：规划总大纲和文献池。
2. `evidence-grounded-chapter-writer`：撰写带证据标记的章节初稿。
3. `reference-integrity-auditor`：审查来源支撑和引用关键词。
4. `engineering-paper-humanizer`：润色中文工程论文表达。
5. `academic-format-cleaner`：修复引用位置、格式、命令和结构问题。

不要在 P0/P1 证据问题尚未解决时执行最终格式清理；应先补证据或降级表述。

## Core Scope

优先检查这些问题：

1. **LaTeX 引用位置**：`\cite{}` 应紧贴被引文字，并位于中文句号、逗号内侧。
2. **LaTeX 命令完整性**：`\cite{}`、`\label{}`、`\ref{}`、`\includegraphics{}` 等命令参数不要跨行断裂。
3. **百分号转义**：正文数字百分号写作 `\%`，避免 `%` 截断行尾。
4. **占位符残留**：清理 `\cite{ref1}`、`\cite{xxx}`、`$\times$` 等临时占位。
5. **公式格式保护**：检查公式环境是否完整，避免把公式、参数符号、单位和编号当作正文润色对象。
6. **列表格式**：检测 `\item \textbf{名词：}` 这类机械清单格式，提示转为连贯段落。

## Workflow

1. 先判断用户是在要求格式检查，而不是正文润色。
2. 运行格式检查脚本：

   ```bash
   python <SKILL_DIR>/scripts/check_format.py <TARGET_FILE>
   python <SKILL_DIR>/scripts/check_format.py <TARGET_FILE> --format markdown
   python <SKILL_DIR>/scripts/check_format.py <TARGET_FILE> --format plain
   ```

3. 根据逐行诊断修复格式问题。
4. 复查同一命令，直到 `error` 清零；`warning/info` 按论文规范和用户偏好处理。

## Non-Goals

不要在本 skill 中处理：

- AI 腔、套话、宣传式表达。
- 中文正文是否自然。
- 中文引号和破折号的语义改写。
- 数据、结论或文献内容的实质性改写。

遇到这些需求时，切换到 `engineering-paper-humanizer`。

## Reference Files

| 文件 | 用途 |
| --- | --- |
| `scripts/check_format.py` | 格式检查入口 |
| `scripts/format_rules.json` | 格式规则数据 |
| `scripts/generate_format_dict.py` | 生成格式规则速查表 |
| `references/format-guide.md` | 格式规则说明 |
