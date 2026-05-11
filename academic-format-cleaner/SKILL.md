---
name: academic-format-cleaner
description: >-
  用于学术文档的格式层清理。用户提到论文格式检查、LaTeX 报错、citation placement、
  Markdown/tex/txt format rules、BibTeX/LaTeX 引用、百分号转义、命令断行、列表格式、
  代码块或数学环境保护时使用。适用于 LaTeX、Markdown 和纯文本草稿的格式收尾；
  不处理正文润色或去 AI 味，这些交给 engineering-paper-humanizer。
---

# Academic Format Cleaner

本 skill 只处理格式层问题，不负责改写正文风格。它通常是 thesis workflow 的最后一道后处理，用来保护命令、公式、引用和 Markdown/LaTeX 结构。

运行脚本需要 Python 3.7 或更高版本。

## 与其他 Thesis Skills 的边界

- `engineering-paper-humanizer`：处理中文工程论文正文、AI 腔、通用中文标点、引号、破折号和表达自然度。
- `academic-format-cleaner`：处理 LaTeX/Markdown/plain text 的格式约束、引用位置、命令保护、结构性格式问题和残留占位符。
- 如果发现 P0/P1 证据问题、缺来源结论或 `[待补来源: ...]` 仍在正文中，先交给 `reference-integrity-auditor` 或移入证据缺口清单，再做最终格式清理。

推荐顺序：

1. `thesis-outline-planner`：规划总大纲和文献池。
2. `evidence-grounded-chapter-writer`：撰写带证据标记的章节初稿。
3. `reference-integrity-auditor`：审查来源支撑和 source marker。
4. `engineering-paper-humanizer`：润色中文工程论文表达。
5. `academic-format-cleaner`：修复引用位置、格式、命令和结构问题。

## 检查范围

优先检查这些问题：

1. **LaTeX 引用位置**：`\cite{}` 应紧贴被引文字，并位于中文句号、逗号内侧；不要孤立成句。
2. **LaTeX 命令完整性**：`\cite{}`、`\label{}`、`\ref{}`、`\includegraphics{}` 等命令参数不要跨行断裂。
3. **百分号转义**：正文数字百分号写作 `\%`，避免 `%` 被当作 LaTeX 注释截断行尾。
4. **占位符残留**：清理 `\cite{ref1}`、`\cite{xxx}`、`$\times$` 等临时占位。
5. **数学和代码环境保护**：检查公式环境是否完整，避免把公式、变量、单位、编号、代码块当作正文润色对象。
6. **列表格式**：检测 `\item \textbf{名词：}` 这类机械清单格式，提示转为连贯段落或符合模板的列表结构。
7. **Markdown 数学块一致性**：同一 Markdown 文件中优先使用一种块级数学格式，例如 fenced `math`、`$$...$$` 或 `\[...\]`，除非模板要求混用。
8. **source marker 格式**：工作稿可使用 `[参考文献]` 和 `[文献题名]` 标记来源，重复题名使用 `[题名 作者 年份]`。最终定稿前再统一转换为学校模板要求的编号引用、脚注或 BibTeX/LaTeX 引用。
9. **缺来源正文残留**：正文中的 `[待补来源: ...]` 属于未清理证据缺口。最终格式清理前应移出正文，放入 `未写入正文的待补资料`、`证据缺口清单` 或项目台账。
10. **标准规范工作标记**：正文中的 `[标准规范: ...]` 不能直接进入最终定稿。已核验标准应改写为正式正文依据并配 `[参考文献]` 或模板要求的引用；未核验标准移入 `证据缺口清单`。

Markdown 数学块、题名 marker、缺来源标记等脚本检查目前主要在 `--format markdown` 下执行。处理 LaTeX 或 plain text 时，按本节规则人工复核同类问题。

## 工作流程

1. 先判断用户要求的是格式检查，而不是正文润色、证据审计或章节写作。
2. 如需直接修改论文主文件，修改前先备份主文件，并在输出中说明备份位置；复制备份默认放在论文项目根目录的 `.thesis-workflow/backups/`。修改完成后，即使已经写回主文件，也要把本轮格式清理结果另存或同步到 `.thesis-workflow/05-format-cleaned.md`。若只返回修复片段且没有进入论文项目工作流，不需要创建备份。
   用户要求生成独立格式清理稿但未指定目录时，默认写入 `.thesis-workflow/05-format-cleaned.md`，不要写入 skill 仓库。
   单独运行本 skill 时，若当前目录、用户指定目录或已识别的论文项目根目录中存在 `.thesis-workflow/`，或用户明确处于论文 workflow 项目中，结束时必须更新 `.thesis-workflow/05-format-cleaned.md` 和必要的 `project-ledger.md`；不要因为用户没有再次说“生成文件”而跳过更新。若 P0/P1 或缺来源定论仍未解决，不生成最终清理稿，只把阻塞项和可安全清理部分写入阶段产物。
3. 如有目标文件，运行格式检查脚本：

   ```bash
   python <SKILL_DIR>/scripts/check_format.py <TARGET_FILE>
   python <SKILL_DIR>/scripts/check_format.py <TARGET_FILE> --format markdown
   python <SKILL_DIR>/scripts/check_format.py <TARGET_FILE> --format plain
   ```

4. 根据逐行诊断修复格式问题；不要改写技术结论、实验数据、公式推导或文献含义。
5. 复查同一文件，直到 `error` 清零；`warning` 和 `info` 按学校模板、论文规范和用户偏好处理。
6. 如果用户提供的是片段而不是文件，直接给出修复后的片段，并简短说明改动类型。

## 不处理的内容

不要在本 skill 中处理：

- AI 腔、套话、宣传式表达。
- 中文正文是否自然。
- 引号、破折号背后的语义重写。
- 数据、结论、文献内容的实质性改写。
- P0/P1 证据缺口、伪造文献或缺来源定论。

遇到正文润色需求时切换到 `engineering-paper-humanizer`；遇到证据问题时先用 `reference-integrity-auditor`。

## 参考文件

| 文件 | 用途 |
| --- | --- |
| `scripts/check_format.py` | 格式检查入口 |
| `scripts/format_rules.json` | 格式规则数据 |
| `scripts/generate_format_dict.py` | 生成格式规则速查表 |
| `references/format-guide.md` | 格式规则说明 |
