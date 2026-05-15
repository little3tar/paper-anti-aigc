---
name: academic-format-cleaner
description: >-
  用于学术文档的格式层清理。用户要求清理/检查/修复格式、修一下格式、整理格式、
  查格式问题、论文格式检查、LaTeX 报错/命令断行/百分号转义、citation placement、
  BibTeX/LaTeX 引用格式、列表格式、代码块或数学环境保护时使用。
  适用于 LaTeX、Markdown 和纯文本草稿的格式收尾；不处理正文润色或去 AI 味，这些交给 engineering-paper-humanizer。
---

# Academic Format Cleaner

## Red Flags（停止并检查）

| AI的想法 | 正确做法 |
|---|---|
| "格式问题很少，目测一下就行" | 必须运行 check_format.py，依赖脚本输出判断 |
| "`[待补来源]` 标记先留着" | 残留标记必须清理或移入证据缺口，不得留到最终稿 |
| "引用位置差不多就行" | `\cite{}` 须紧贴被引文字，位于中文句号、逗号内侧 |
| "P0/P1 还在，但只做格式检查没事" | 格式清理前检查 status.json，P0/P1 > 0 时拒绝继续 |
| "部分格式问题不在脚本检测范围" | 脚本未覆盖的问题按本 skill 规则人工复核 |
| "marker 题名改了也不影响格式" | `[文献题名]` 方括号内题名必须与原始草稿一致，缩写/翻译/改写视为 P2 |
| "`“` 是 JSON 的事，格式不用管" | Unicode 转义序列必须还原为实际字符——`“`→`"`、`”`→`"`、`‘`→`'`、`’`→`'` 等 |

本 skill 只处理格式层问题，不负责改写正文风格。它通常是 thesis workflow 的最后一道后处理，用来保护命令、公式、引用和 Markdown/LaTeX 结构。

运行脚本需要 Python 3.7 或更高版本。

## 与其他 Thesis Skills 的边界

- `engineering-paper-humanizer`：处理中文工程论文正文、AI 腔、通用中文标点、引号、破折号和表达自然度。
- `academic-format-cleaner`：处理 LaTeX/Markdown/plain text 的格式约束、引用位置、命令保护、结构性格式问题和残留占位符。
- 如果发现 P0/P1 证据问题、缺来源结论或 `[待补来源: ...]` 仍在正文中，先交给 `reference-integrity-auditor` 或移入证据缺口清单，再做最终格式清理。
- 启动格式清理前，检查 `.thesis-workflow/status.json`（门控规则遵循 workflow §强制串行规则第6条）：若 `p0_count` 或 `p1_count` > 0，或 `next_allowed` 不为 `"format-cleaner"` 或 `"next-chapter"`，拒绝继续并提示用户先完成上游审计和润色。若 `next_allowed` 为 `"fix-evidence"` 说明审计已发现问题但尚未修复，拒绝继续。若 `next_allowed` 为 `"humanizer"` 说明润色尚未完成，拒绝继续。若文件不存在，说明审计阶段未运行，拒绝继续。

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
11. **用户材料残留标记**：`[用户材料: ...]`、`[Mxx]`、`[内部参考: ...]` 等内部工作标记不得出现在最终定稿中。检测到后强制清除标记本身，保留实质性内容（设计假设、推导过程或工程解释）。
12. **marker 内容完整性**（润色后核对）：对照 `.thesis-workflow/02-chapter-draft.md`（内容权威源）中的 source marker 清单，检查主文件（`main.md`/`main.txt` 或 `main-chX.md`/`main-chX.txt`）中 `[文献题名]` 方括号内的题名文字是否保持原样。被缩写、翻译、改写或缺失的 marker 视为 P2 问题，需从原始草稿恢复。此项在 LaTeX、Markdown 和 plain text 中均需人工复核。注意：`04-humanized.md` 是变更清单（非全文副本），不能用作 marker 完整性校验源。
13. **Unicode 转义序列还原**：最终输出稿中不得出现 Unicode 转义序列。中文引号 `“` `”` 必须还原为 `"` `"`，单引号 `‘` `’` 还原为 `'` `'`，其他可见字符的转义序列同样还原为实际 Unicode 字符。此项在 LaTeX、Markdown 和 plain text 中均需检查。

Markdown 数学块、题名 marker、缺来源标记等脚本检查目前主要在 `--format markdown` 下执行。处理 LaTeX 或 plain text 时，按本节规则人工复核同类问题。

## 工作流程

1. 先判断用户要求的是格式检查，而不是正文润色、证据审计或章节写作。
2. 如需直接修改论文主文件，修改前先通过 `engineering-paper-humanizer/scripts/git_snapshot.py <主文件>` 创建备份。修改完成后将本轮格式修复记录（变更清单，非全文副本）写入 `.thesis-workflow/05-format-cleaned.md`，最终清理后文本写入主文件（单文件模式 `main.md` / `main.txt`，拆分模式 `main-chX.md` / `main-chX.txt`）。
   文件产出规则遵循 workflow §输出与文件安全。本阶段产物为 `.thesis-workflow/05-format-cleaned.md`（格式修复记录，非全文副本）。
3. 如有目标文件，运行格式检查脚本：

   ```bash
   python <SKILL_DIR>/scripts/check_format.py <TARGET_FILE>
   python <SKILL_DIR>/scripts/check_format.py <TARGET_FILE> --format markdown
   python <SKILL_DIR>/scripts/check_format.py <TARGET_FILE> --format plain
   ```

4. 根据逐行诊断修复格式问题；不要改写技术结论、实验数据、公式推导或文献含义。
5. **核对 marker 内容完整性**：读取原始草稿（`.thesis-workflow/02-chapter-draft.md`）和主文件（`main.md`/`main.txt` 或 `main-chX.md`/`main-chX.txt`），提取两份文件中所有 `[文献题名]` marker 的题名列表进行比较。题名被缩写、翻译、改写或缺失的，标记为 P2 并从原始草稿恢复正确题名。注意：`04-humanized.md` 只存变更清单不含全文，不可用作对比源。若主文件不存在则跳过此步。
6. 复查同一文件，直到 `error` 清零；`warning` 和 `info` 按学校模板、论文规范和用户偏好处理。
7. 如果用户提供的是片段而不是文件，直接给出修复后的片段，并简短说明改动类型。

格式清理完成后，更新 `.thesis-workflow/status.json`：将 `stage` 设为 `"format-cleaned"`、`next_allowed` 设为 `"next-chapter"`，放行下一章写作或全流程主文件写入。

## 不处理的内容

本 skill 只处理格式层。AI 腔、正文润色、证据审计分别交给 humanizer 和 auditor。

## 参考文件

| 文件 | 用途 |
| --- | --- |
| `scripts/check_format.py` | 格式检查入口 |
| `scripts/format_rules.json` | 格式规则数据 |
| `scripts/generate_format_dict.py` | 生成格式规则速查表 |
| `references/format-guide.md` | 格式规则说明 |
