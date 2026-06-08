---
name: academic-format-cleaner
description: >-
  用于学术文档的格式层清理。用户要求清理/检查/修复格式、修一下格式、整理格式、
  查格式问题、检查以下文本格式（粘贴文本）、论文格式检查、LaTeX 报错/命令断行/百分号转义、citation placement、
  BibTeX/LaTeX 引用格式、列表格式、代码块或数学环境保护时使用。
  适用于 LaTeX、Markdown 和纯文本草稿的格式收尾；不处理正文润色或去 AI 味，这些交给 engineering-paper-humanizer。
  用户在消息中直接粘贴待检查文本时，自动进入独立模式，跳过工作流门控。
---

# Academic Format Cleaner

## Red Flags（停止并检查）

| AI的想法 | 正确做法 |
|---|---|
| "格式问题很少，目测一下就行" | 必须运行 check_format.py，依赖脚本输出判断 |
| "`[待补来源]` 标记先留着" | 残留标记必须清理或移入证据缺口，不得留到最终稿 |
| "引用位置差不多就行" | `\cite{}` 须紧贴被引文字，位于中文句号、逗号内侧 |
| "P0/P1 还在，但只做格式检查没事" | 工作流模式下检查 status.json，P0/P1 > 0 时拒绝继续（validation mode 不在此限，详见 workflow §强制串行规则第6条）；独立模式不受此限 |
| "humanizer 已经跑过了，marker 不会出错，不用逐项核对" | 对照 draft.md 逐一核对主文件中每个 `[文献题名]` marker 的题名文字，验证未被缩写、翻译或改写。即使 humanizer 已确认 marker 完整性，format-cleaner 也必须独立逐项校对，不得信任上游 |
| “ 是 JSON 的事，格式不用管” | Unicode 转义序列必须还原：HTML 实体 &quot; &ldquo; 等、Unicode 转义 “ “ ‘ ‘ 等，全部还原为实际 Unicode 字符 |

只处理格式层问题，不负责改写正文风格。作为 thesis workflow 最后一道后处理，保护命令、公式、引用和 Markdown/LaTeX 结构。

运行脚本需要 Python 3.7 或更高版本。

## 与其他 Thesis Skills 的边界

- `engineering-paper-humanizer`：处理中文工程论文正文、AI 腔、通用中文标点、引号、破折号和表达自然度。
- `academic-format-cleaner`：处理 LaTeX/Markdown/plain text 的格式约束、引用位置、命令保护、结构性格式问题和残留占位符。
- 如果发现 P0/P1 证据问题、缺来源结论或 `[待补来源: ...]` 仍在正文中，先交给 `reference-integrity-auditor` 或移入证据缺口清单，再做最终格式清理。
- 启动前先判断运行模式（见 §运行模式）：
  - **独立模式**（用户粘贴了待检查文本）→ 跳过门控检查，直接进行格式检查。
  - **工作流模式**（用户引用论文文件）→ 读取 `.thesis-workflow/chapters/chX/status.json`，按 workflow §强制串行规则第6条执行门控检查：P0/P1 未清零或 `next_allowed` 不匹配则拒绝继续。独立模式不受此限。完整规则和放行条件见 workflow §强制串行规则第6条，本处不重述具体取值枚举。

完整阶段顺序见 workflow SKILL.md §阶段顺序。

## 检查范围

优先检查这些问题：

1. **LaTeX 引用位置**：`\cite{}` 应紧贴被引文字，并位于中文句号、逗号内侧；不要孤立成句。
2. **LaTeX 命令完整性**：`\cite{}`、`\label{}`、`\ref{}`、`\includegraphics{}` 等命令参数不要跨行断裂。
3. **百分号转义**：正文数字百分号写作 `\%`，避免 `%` 被当作 LaTeX 注释截断行尾。
4. **占位符残留**：清理 `\cite{ref1}`、`\cite{xxx}`、`$\times$` 等临时占位。
5. **数学和代码环境保护**：检查公式环境是否完整，避免把公式、变量、单位、编号、代码块当作正文润色对象。
6. **列表格式**：检测 `\item \textbf{名词：}` 这类机械清单格式，提示转为连贯段落或符合模板的列表结构。
7. **Markdown 数学块一致性**：同一 Markdown 文件中优先使用一种块级数学格式，例如 fenced `math`、`$$...$$` 或 `\[...\]`，除非模板要求混用。
8. **source marker 格式与残留标记清理**：marker 类型定义和残留标记清单见 chapter-writer 参考文件 `citation-key-rules.md`。本阶段负责清除正文中的残留工作标记：`[待补来源: ...]`（移入证据缺口清单）、`[标准规范: ...]`（已核验转正式引用，未核验移入缺口清单）、`[用户材料: ...]` 和 `[Mxx]`（保留实质内容，清除标记本身）。`[文献题名]` marker 保留至主文件。
9. **marker 内容完整性**（润色后核对）：对照 `.thesis-workflow/chapters/chX/draft.md`（内容权威源）中的 source marker 清单，检查主文件中 `[文献题名]` 方括号内的题名文字是否保持原样。被缩写、翻译、改写或缺失的 marker 视为 P2 问题，需从原始草稿恢复。注意：`chapters/chX/humanized.md` 是变更清单（非全文副本），不能用作 marker 完整性校验源。
10. **Unicode 转义序列还原**：最终输出稿中不得出现 Unicode 转义序列。中文引号 `”` `”` 必须还原为 `”` `”`，单引号 `’` `’` 还原为 `’` `’`，其他可见字符的转义序列同样还原为实际 Unicode 字符。此项在 LaTeX、Markdown 和 plain text 中均需检查。

Markdown 数学块、题名 marker、缺来源标记等脚本检查目前主要在 `--format markdown` 下执行。处理 LaTeX 或 plain text 时，按本节规则人工复核同类问题。

## 运行模式

根据用户输入来源自动判断模式，无需用户手动指定：

| 场景 | 判断依据 | 模式 |
|---|---|---|
| 用户粘贴文本到消息中（如"检查以下文本格式：……"） | 消息中包含待检查的完整文本片段 | **独立模式** |
| 用户指定论文文件且 status.json 存在 | 消息中引用文件路径，且 `.thesis-workflow/chapters/chX/status.json` 存在 | **工作流模式**（validation mode 下 P0/P1 可不为 0，见 workflow §强制串行规则第6条） |
| 用户引用文件路径但 status.json 不存在 | 消息中引用文件路径，但对应章无 status.json | **提示用户**：先完成上游阶段（审计→润色），用户确认后可降级为独立模式运行 |

**独立模式**：不检查 `status.json`，不写入产物文件。只运行格式检查脚本和规则修复，结果直接返回。

**工作流模式**：遵循下方完整流程，包括门控检查、备份、产物落盘和 `status.json` 更新。

## 工作流程

1. 先判断运行模式（见 §运行模式）和用户目标：格式检查，而不是正文润色、证据审计或章节写作。
   - **独立模式**：跳过产物文件写入和备份步骤。运行检查脚本 → 修复问题 → 返回结果。
   - **工作流模式**：执行以下步骤。
2. 如需直接修改论文主文件，修改前先通过 `scripts/git_snapshot.py <主文件>` 创建备份。修改完成后将本轮格式修复记录（变更清单，非全文副本）写入 `.thesis-workflow/chapters/chX/format-cleaned.md`。主文件写入由 workflow 全流程完成仪式统一执行，不在本阶段单独写入。
   文件产出规则遵循 workflow §输出与文件安全。本阶段产物为 `.thesis-workflow/chapters/chX/format-cleaned.md`（格式修复记录，非全文副本）。
3. 如有目标文件，运行格式检查脚本：

   ```bash
   python <SKILL_DIR>/scripts/check_format.py <TARGET_FILE>
   python <SKILL_DIR>/scripts/check_format.py <TARGET_FILE> --format markdown
   python <SKILL_DIR>/scripts/check_format.py <TARGET_FILE> --format plain
   ```

   加 `--fix --format plain` 可自动完成 Markdown → 纯文本剥离（去除标题标记、加粗/斜体、行内代码反引号、链接、列表标记、引用、代码围栏、水平线，表格转空格对齐，Mermaid/DOT 图表代码块保留围栏，`$$` 公式保留语法）。详见 `references/format-guide.md` 自动转换小节。

4. 根据逐行诊断修复格式问题；不要改写技术结论、实验数据、公式推导或文献含义。
5. **核对 marker 内容完整性**：读取原始草稿（`.thesis-workflow/chapters/chX/draft.md`）和主文件（`main-chX.md` / `main-chX.txt` / `main-chX.tex`），提取两份文件中所有 `[文献题名]` marker 的题名列表进行比较。题名被缩写、翻译、改写或缺失的，标记为 P2 并从原始草稿恢复正确题名。注意：`chapters/chX/humanized.md` 只存变更清单不含全文，不可用作对比源。若主文件不存在则跳过此步。
6. 复查同一文件，直到 `error` 清零；`warning` 和 `info` 按学校模板、论文规范和用户偏好处理。
7. 如果用户提供的是片段而不是文件，直接给出修复后的片段，并简短说明改动类型。

格式清理完成后（工作流模式），更新 `.thesis-workflow/chapters/chX/status.json`：将 `stage` 设为 `"format-cleaned"`、`next_allowed` 设为 `"next-chapter"`，放行下一章写作或全流程主文件写入。独立模式不更新 `status.json`。

**format-cleaned.md 最低记录要求**（工作流模式）：
- Marker 逐条核对结果表（至少列出：题名原文 vs 主文件中题名，标记是否一致）
- Unicode 转义序列检查结论（检出数量 + 修复数量）
- `check_format.py` 最终 error 数（必须为 0）
- 禁止只写"格式检查通过"这类无信息量的单句记录

## 不处理的内容

只处理格式层。AI 腔、正文润色、证据审计分别交给 humanizer 和 auditor。

## 参考文件

| 文件 | 用途 |
| --- | --- |
| `scripts/check_format.py` | 格式检查入口（脚本内部使用 `format_rules.json` 规则集） |
| `references/format-guide.md` | 格式规则说明 |
| `scripts/git_snapshot.py` | 智能备份脚本（修改主文件前创建备份） |
| 见 chapter-writer 参考文件 `citation-key-rules.md` | marker 类型定义和残留标记清单（`[待补来源]`/`[标准规范]`/`[用户材料]`/`[Mxx]`/`[设计假设]`/`[待核实]`/`[计算导出]` 等七类标记的清除与转换） |