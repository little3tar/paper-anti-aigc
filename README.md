# Paper Anti-AIGC

一套面向中文工程类毕业论文的 AI 辅助写作工作流与 Skills，根据自己对于论文写作的理解，在 Codex 的帮助下创建，并参考成型项目优化，覆盖大纲规划、证据驱动章节撰写、来源审计、正文润色到格式收尾五个阶段（任务书解析融入大纲规划阶段）。支持 Claude Code 等兼容 `SKILL.md` 的工具。

> 本项目仅供学术写作组织、证据核验、表达润色和格式自检参考。请遵守所在学校或机构的学术诚信规范。

## Skills

| Skill | 用途 |
| --- | --- |
| `thesis-writing-workflow` | 工作流路由器，管理确认点、输出格式、备份和多 skill 协作 |
| `thesis-outline-planner` | 从任务书生成证据驱动的大纲、文献池、图表计划 |
| `evidence-grounded-chapter-writer` | 基于大纲和证据撰写章节，维护 source marker 和证据缺口 |
| `reference-integrity-auditor` | 审计 P0/P1 证据问题、source marker、公式可复现性 |
| `engineering-paper-humanizer` | 润色中文工程论文正文，降 AI 腔，处理中文标点 |
| `academic-format-cleaner` | 格式收尾：引用位置、命令保护、数学块和残留标记清理 |
| `docx-translator` | 将 Word 文档(.docx)内容翻译为中文，保留原文档格式（独立 skill，非论文工作流流程的一部分） |

## 工作流

```
任务书 / 题目
    │
    ▼
thesis-outline-planner         ← 大纲、文献池、图表计划
    │
    ▼
evidence-grounded-chapter-writer  ← 章节草稿 + 证据标记
    │
    ▼
reference-integrity-auditor    ← 证据审计、P0/P1 分类
    │
    ▼
engineering-paper-humanizer    ← 降 AI 腔、润色正文
    │
    ▼
academic-format-cleaner        ← 格式收尾、引用位置清理
```

也可从中间任意一步进入：

| 如果你有…… | 直接用…… |
| --- | --- |
| 任务书、导师要求 | `thesis-outline-planner` |
| 已有草稿 | `reference-integrity-auditor` |
| 已审计通过的段落 | `engineering-paper-humanizer` |
| 已定稿文本 | `academic-format-cleaner` |
| 组合任务 | `thesis-writing-workflow` 路由 |

## 文献管理

推荐 [Zotero](https://www.zotero.org/) + [cookjohn/zotero-mcp](https://github.com/cookjohn/zotero-mcp)，让 AI 助手检索本地文献库的元数据、全文、笔记和标注。

Zotero MCP 不可用时，工作流退回到 `.bib`、`.ris`、`.csv`、PDF 文件夹和可靠网络来源。

## 安装

**1. 获取仓库**

```bash
git clone https://github.com/little3tar/paper-anti-aigc.git
cd paper-anti-aigc
```

或从 [Releases](https://github.com/little3tar/paper-anti-aigc/releases) 下载压缩包解压。

**2. 将 `skills/` 和 `hooks/` 复制到论文项目的对应路径：**

**Claude Code**

```bash
cp -r skills/* your-project/.claude/skills/
cp -r hooks/* your-project/.claude/hooks/
cp settings.json your-project/.claude/settings.json
```

> **关于 settings.json**：Claude Code 通过此文件启用 PreToolUse 钩子（主文件保护 + 阶段门控）和 SessionStart 钩子（会话启动时注入工作流状态）。如果不复制此文件，钩子保护机制不会生效，仅 AI 工作流层面的规则会执行。`hooks/hooks.json` 已废弃并移除。

**OpenCode**

```bash
cp -r skills/* your-project/.opencode/skills/
```

> OpenCode 支持 SKILL.md 格式的 skills，但 **不支持 Claude Code 的 Hook 协议**（PreToolUse/PostToolUse/Stop 事件格式不同）。hooks 目录仅供 Claude Code 使用，OpenCode 下无需复制。

**Cursor / 其他**

```bash
cp -r skills/* your-project/.agents/skills/
```

> Cursor 的 Hook 配置使用 `~/.cursor/hooks.json`（camelCase 事件名 + 不同 JSON schema），与 Claude Code 的 `settings.json` 格式不兼容。hooks 目录仅供 Claude Code 使用，Cursor 下无需复制。

> **关于 `skills/*/agents/openai.yaml`**：这些文件是 OpenCode/Cursor 兼容层（`interface.display_name` / `short_description` / `default_prompt`），Claude Code 忽略它们。Claude Code 的 agent 定义应放置在 `.claude/agents/*.md`。

## 快速开始

安装完成后，在论文项目目录下启动 Claude Code，根据你的情况选择一句发给 AI 即可启动。

### 从零开始（有任务书）

```
我有一份毕业设计任务书，帮我按论文工作流从大纲开始规划。
先确认输出格式和主文件位置，然后逐步推进。
```

工作流会自动引导你完成：大纲规划 → 章节写作 → 证据审计 → 润色去 AI 味 → 格式收尾。

### 只规划大纲

```
这是我的论文题目和导师要求：

[在此粘贴你的任务书或导师要求]

帮我出论文大纲，包括每章的文献需求、图表计划和公式需求判断。
```

### 已有草稿，需要审计和润色

```
我的论文第 2 章草稿在 output/main-ch2.md，帮我审计证据完整性。
审计通过后再润色去 AI 味。
```

如果草稿还没审计过，AI 会先运行 `reference-integrity-auditor`，P0/P1 清零后自动进入润色。

### 只润色一段文字（不涉及工作流）

直接把文字贴给 AI：

```
润色以下文本，降低 AI 痕迹但保留技术参数：

[在此粘贴你的文字]
```

> 直接粘贴文本时自动进入独立模式，不检查工作流状态，结果直接返回不落盘。

### 继续之前的工作

如果你的项目已有 `.thesis-workflow/` 目录，AI 会在启动时自动读取各章进度，直接告诉它"继续"即可：

```
继续写论文
```

AI 会从上次中断的阶段接着推进。

### 常见问题

**Q: AI 会不会自动写主文件，覆盖我的修改？**
不会。草稿始终写入 `.thesis-workflow/chapters/chX/draft.md`，主文件（`output/main-chX.md`）只在全部五个阶段完成且你显式确认后才更新。

**Q: 没有 Zotero 能用吗？**
能。工作流会自动退回到 `.bib` 文件、PDF 和网络检索，但推荐安装 Zotero + zotero-mcp 以获得最佳文献管理体验。

**Q: 中途可以换工具吗？**
可以。所有进度保存在 `.thesis-workflow/` 的纯文本文件中，不依赖特定工具。

### 使用心得

这套工作流的本意是自动化产出一篇 LaTeX 论文，但我们学校只提供了不算完整的 Word 模板，要让 AI 编写完全符合模板格式的 Word 内容依然比较困难。最后我直接使用工作流产出的 `.txt` 文件，自己复制粘贴到 Word 模板里，反而省了很多事。

关于 LaTeX，最初写论文时老师没说最后必须交 Word，我自作主张用了一段时间 LaTeX，但后续确认必须使用 Word，就中途放弃了 LaTeX 路线。因此 skills 里的 LaTeX 格式检查（`check_format.py`）可能并不完善，如果你用 LaTeX 写论文，格式方面建议自己再仔细过一遍。

虽说最初整理这套 skills 的目标是尽可能自动化，但直到现在我的论文快结束了，在使用过程中不断发现和解决问题，依然没能做到完全自动化，AI 还是会在各种意想不到的地方出错。所以**推荐每一步结束后至少做一次人工检查**，不要把 AI 的输出直接当定稿。

**关于 AI 检测率**：经过实践，完整按工作流走完全程，且每一步都进行人工把关（尤其是润色阶段），最终 AI 率能降到二十多。如果不满意，可以把 AI 检测报告中较为严重的段落单独再走一次润色 skill——工作流也支持这种用法（用户粘贴文本，直接进入独立润色模式）。本人论文 7 万字，经 [SpeedAI 模拟维普 AI 检测](https://speedai.com/aigc-detection) 测试，从最初检测 AI 率降到 5% 左右。根据周围同学反馈，SpeedAI 的 AI 率通常比学校定制的维普检测偏高一些，实际学校检测结果可能更低。当然，各学校定制的检测数据库可能有差异，该网站也宣称与官方检测结果一般在 10% 以内。

作者只是机械类本科生，这套工作流是一边用一边完善的，做出的东西可能较为粗糙。写作中没有遇到的问题也就没有加强相关规则，局限性在所难免。也欢迎提 [issue](https://github.com/little3tar/paper-anti-aigc/issues) 和 [PR](https://github.com/little3tar/paper-anti-aigc/pulls)。

## 运行产物

真实论文工作流默认使用论文项目根目录下的 `.thesis-workflow/`，各阶段产物说明如下。

### 目录总览

```text
.thesis-workflow/
├── main-tex-context.md        ← 论文主文件结构地图
├── materials-inventory.md     ← 用户材料编目清单
├── literature-pool.md         ← 文献池全表（含 ZoteroKey 映射，分组管理）
├── figure-data-manifest.md    ← 图表数据溯源清单（数据文件、生成脚本、输出格式）
├── calculation-records.md     ← 数值唯一权威源（公式代入、参数来源、标准选型）
├── operations-log.md          ← 操作日志（项目检查、章节清除等一次性操作，只追加）
├── outline.md                 ← 阶段 1：总大纲（章→节→小节）
│
├── chapters/                  ← 按章归档的阶段产物（每章独立，不互相覆盖）
│   ├── ch1/
│   │   ├── detailed-outline.md  ←   阶段 2 前置：段落级写作细纲（用户确认后）
│   │   ├── status.json          ←   本章门控状态（P0/P1/P2 + next_allowed，权威）
│   │   ├── draft.md           ←   阶段 2：章节正文草稿（内容权威源）
│   │   ├── audit.md           ←   阶段 3：审计报告 + 文献修正记录
│   │   ├── humanized.md       ←   阶段 4：润色操作记录（非全文副本）
│   │   ├── format-cleaned.md  ←   阶段 5：格式修复记录（非全文副本）
│   │   └── literature-notes.md←   文献笔记缓存（按章存储，随章保留）
│   └── chN/ ...
│
├── ledger/                    ← 项目台账（拆分后，各子文件独立读写）
│   ├── facts.md               ←   已确认设计参数、引用标准、MC51 公开数据
│   ├── decisions.md           ←   已确认决策（输出格式/路径/引用方案）
│   ├── chapter-status.md      ←   各章 6 阶段完成状态
│   └── questions.md           ←   结构化待确认问题
│
├── evidence/                  ← 用户提供材料的物理存放
│   ├── task-book/             ←   任务书、设计说明、开题报告
│   ├── reference-materials/   ←   用户提供的论文、手册、教材副本
│   ├── user-data/             ←   用户自算数据、实验记录、仿真结果
│   ├── user-figures/          ←   用户自制的图、照片、截图
│   ├── user-videos/           ←   用户提供的视频、动画、演示录像
│   ├── user-code/             ←   用户提供的程序、脚本
│   ├── advisor-notes/         ←   导师批注、会议记录
│   ├── standards-specs/       ←   用户提供的标准规范文件
│   └── zotero-export/         ←   Zotero 导出的 .bib 文件（文献信息校验基准）
│
├── generated-figures/         ← AI 生成的图（Mermaid/matplotlib/DOT/提示词渲染产物，可重新生成）
│
├── backups/                   ← 主文件备份（锚点备份不限）
```
> **主文件输出**：最终章文件默认输出到论文项目根目录下的 `output/` 子目录（如 `output/main-ch1.md`），避免大量章文件散落根目录。用户指定位置或模板要求位置优先。

### 各文件/目录说明

#### 项目台账（ledger/）

已拆分为 `ledger/` 子目录，各 skill 直接读写对应文件，无需汇总索引。

| 文件 | 记录内容 | 关键字段 |
| --- | --- | --- |
| `ledger/facts.md` | 已确认设计参数、引用标准、MC51公开数据 | 参数、来源、性质(A/B/C)、计算记录ID |
| `ledger/decisions.md` | 输出格式、文件路径、引用方案等用户确认决策 | 日期、决策、理由、影响范围 |
| `ledger/chapter-status.md` | 各章阶段完成状态（6 列：大纲/细纲/草稿/审计/润色/格式） | 章节、大纲、细纲、草稿、审计、润色、格式 |
| `ledger/questions.md` | 结构化待确认问题 | 编号、问题、阻塞章节、优先级、状态 |

**数值单一权威源**：计算类数值（缸径、推力等）只在 `calculation-records.md` 中定义。`ledger/facts.md` 只记录参数名和关联计算记录 ID，不复制数值。

状态标签：`confirmed`、`draft`、`needs-source`、`needs-user-data`、`derived`、`superseded`。

#### 阶段产物

| 文件 | 产生阶段 | 内容 | 更新时机 |
| --- | --- | --- | --- |
| `outline.md` | thesis-outline-planner | 总大纲（章→节→小节） | 大纲确认后 |
| `literature-pool.md` | thesis-outline-planner | 文献池全表（含 ZoteroKey，分组管理） | 大纲确认后 |
| `chapters/chX/detailed-outline.md` | evidence-grounded-chapter-writer | 章节细纲（段落级写作点） | 细纲确认后 |
| `chapters/chX/draft.md` | evidence-grounded-chapter-writer | 第 X 章正文草稿（内容权威源） | 每章草稿完成后 |
| `chapters/chX/audit.md` | reference-integrity-auditor | 第 X 章审计报告 + 文献修正记录 | 审计完成后 |
| `chapters/chX/humanized.md` | engineering-paper-humanizer | 第 X 章润色操作记录（非全文副本，最终文本写入 main-chX.md/txt/tex） | 润色完成后 |
| `chapters/chX/format-cleaned.md` | academic-format-cleaner | 第 X 章格式修复记录（非全文副本，最终文本写入 main-chX.md/txt/tex） | 格式清理完成后 |
| `operations-log.md` | 各阶段 | 批量操作/项目检查/章节清除记录（只追加） | 批量操作后 |

#### 工作辅助文件

| 文件 | 用途 | 生命周期 |
| --- | --- | --- |
| `chapters/chX/literature-notes.md` | Zotero 文献笔记/标注分批缓存，写作和审计阶段引用 | 写作创建，随章保留 |
| `figure-data-manifest.md` | 图表级数据溯源：数据文件路径、真实/mock、生成脚本、输出格式 | 大纲建框架 → 写作填充 → 审计校验；持久保留 |
| `calculation-records.md` | 计算底稿：公式、代入过程、参数来源、标准选型、状态 | 写作创建 → 审计校验 → 参数变更时标 superseded 追加新行 |

#### status.json（门控）

**按章存储**：`.thesis-workflow/chapters/chX/status.json` 为本章权威门控状态。

按章 `chapters/chX/status.json` 格式：

```json
{
    "stage": "audited",
    "chapter": "chX",
    "timestamp": "2026-05-13T22:00:00",
    "p0_count": 0,
    "p1_count": 0,
    "p2_count": 3,
    "green_paragraphs": ["§2.1", "§3.2"],
    "blocked_paragraphs": ["§2.3"],
    "next_allowed": "humanizer",
    "notes": ""
}
```

- `stage`：当前所处阶段（`audited` / `humanized` / `format-cleaned`）
- `p0_count` / `p1_count` / `p2_count`：审计问题计数（p2_count 来自审计报告）
- `green_paragraphs` / `blocked_paragraphs`：humanizer 使用，由 auditor 写入
- `next_allowed` 取值：`"fix-evidence"` / `"humanizer"` / `"format-cleaner"` / `"next-chapter"`
- P0/P1 > 0 时，`next_allowed` 强制为 `"fix-evidence"`，humanizer 和 format-cleaner **硬性阻断**
- 前一章未完成 humanizer+format-cleaner（`next_allowed` 不为 `"next-chapter"`）时，**禁止开始下一章**

#### evidence/（用户材料）

用户提供的任务书、参考资料、数据、图纸、导师批注等，按类型分目录存放。无信息量文件名（如 `IMG_0001.jpg`）须重命名为描述性名称后再整理。同名冲突附加时间戳区分；二进制文件直接移动，文本文件统一转 UTF-8。`user-videos/` 存放用户提供的视频和动画，与 `user-figures/`（图片/照片/截图）分开放置。`user-code/` 存放用户提供的程序、脚本（如 MATLAB 仿真代码、Python 数据处理脚本），与 `generated-figures/` 中 AI 生成的代码分离。

所有材料在 `materials-inventory.md` 中编目：

| ID | 文件名 | 类型 | 路径 | 提取的关键信息 | 数据性质 | 适用章节 | 消化方式 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | task-book.pdf | 任务书 | evidence/task-book/ | 设计目标、约束 | — | 全文 | 规划输入 |
| M02 | motor-datasheet.pdf | 数据表 | reference-materials/ | 额定 15kW | A | §2.3 | 待查外部源 |

> 用户材料仅供内部参考，**不作为正式引用进入正文**。正文中不得出现 `[用户材料: ...]` 或 `[Mxx]` 标记。

`zotero-export/` 存放从 Zotero 导出的 `.bib` 文件，作为审计阶段校验文献信息（题名、作者、年份）准确性的基准。

#### backups/

修改论文主文件前由 `git_snapshot.py` 自动创建。优先使用 Git 分支备份，回退到文件复制备份。锚点备份（`--anchor`）永不自动淘汰。

#### ledger/（台账子目录）

`project-ledger.md` 已拆分为 `ledger/` 下的独立文件（facts/decisions/chapter-status/questions），各自独立读写，无需汇总索引。

#### chapters/chX/detailed-outline.md（章节细纲）

每章的段落级细纲按章存放（`chapters/chX/detailed-outline.md`），写作前由 chapter-writer 生成并经用户确认。总大纲 `outline.md` 只保留到小节标题层级。

#### literature-pool.md（文献池全表）

从 `outline.md` 分离的 60 条文献全表，6 组分类，含 ZoteroKey 映射。大纲中只保留分组摘要。

#### operations-log.md（操作日志）

批量操作、项目检查和重大变更记录。只追加，不修改已有记录。

#### validation/

仅在验证/测试模式下使用，存放合成输入和验证产物，不参与真实论文流程。

## 脚本

全部脚本只依赖 Python 标准库（≥3.7）。DOCX 翻译脚本（`apply_translations.py`、`export_paragraphs.py`）额外依赖 `python-docx`。

### 正文检查（降 AI 腔 + 中文标点）

```bash
python skills/engineering-paper-humanizer/scripts/check_text.py paper.tex
python skills/engineering-paper-humanizer/scripts/check_text.py draft.md   --format markdown
python skills/engineering-paper-humanizer/scripts/check_text.py notes.txt  --format plain
```

### 格式检查（引用位置 + LaTeX 命令 + 残留标记）

```bash
python skills/academic-format-cleaner/scripts/check_format.py paper.tex
python skills/academic-format-cleaner/scripts/check_format.py draft.md   --format markdown
python skills/academic-format-cleaner/scripts/check_format.py notes.txt  --format plain
```

### 规则速查表

```bash
python skills/engineering-paper-humanizer/scripts/generate_dict.py
python skills/academic-format-cleaner/scripts/generate_format_dict.py
```

### 智能备份

```bash
python skills/thesis-writing-workflow/scripts/git_snapshot.py paper.tex
python skills/thesis-writing-workflow/scripts/git_snapshot.py paper.tex --anchor
python skills/thesis-writing-workflow/scripts/git_snapshot.py --list
python skills/thesis-writing-workflow/scripts/git_snapshot.py --rollback paper.tex
```

### LaTeX 项目生成

格式清理完成后，可通过 workflow router 的 `latex-output-guide.md` 将 Markdown 章节转换为 LaTeX 项目（`main.tex` + 章节 `.tex` 文件 + `references.bib`），支持学校模板检测和 `ctexart` 默认模板。

### DOCX 翻译

`docx-translator` 不参与论文写作流程，是独立的文档翻译工具。主要用途是将外文论文、技术文档等翻译为中文并保留原始 Word 格式。

> 英文论文大多只有 PDF 文件，需要先转换为 docx 格式。推荐使用 [iLovePDF](https://www.ilovepdf.com/pdf_to_word) 等在线工具将 PDF 转为 docx，然后手动优化格式（修正表格错位、公式丢失等），最后通过 agent 翻译出成品。

```bash
# 导出段落列表
python skills/docx-translator/scripts/export_paragraphs.py input.docx paragraphs.txt

# 应用翻译到文档
python skills/docx-translator/scripts/apply_translations.py input.docx translations_b64.json output.docx
```

## 测试

`tests/` 用于脚本和规则的回归测试，修改规则或脚本后建议运行：

```bash
python -m unittest discover -s tests
```

`evals/` 用于 skill 触发边界检查，验证 SKILL.md 的 description 是否能被正确匹配：

```bash
# 触发评估配置文件：evals/trigger-evals.json
```

`tests/` 和 `evals/` 仅供 skills 仓库维护使用，不参与论文项目运行，不需要复制到论文项目中。

## 项目演进

本项目从单个 skill 逐步扩展为完整的七 skill 工作流。以下里程碑分支保留了各阶段的完整代码快照：

| 分支 | 提交 | 阶段 | 包含内容 |
|---|---|---|---|
| [`single-skill`](https://github.com/little3tar/paper-anti-aigc/tree/single-skill) | `7493a67` | 1 个 skill | `engineering-paper-humanizer` — 正文润色与去 AI 腔 |
| [`two-skills`](https://github.com/little3tar/paper-anti-aigc/tree/two-skills) | `69a67c1` | 2 个 skills | + `academic-format-cleaner` — 格式层清理 |
| `main` | — | 7 个 skills | + `thesis-writing-workflow`、`thesis-outline-planner`、`evidence-grounded-chapter-writer`、`reference-integrity-auditor`、`docx-translator` |

```bash
# 查看各阶段代码
git checkout single-skill   # 仅润色去 AI 腔
git checkout two-skills     # 润色 + 格式清理
```

## 致谢

本项目受以下项目启发：

- [Norman-bury/research-writing-skill](https://github.com/Norman-bury/research-writing-skill) — 研究写作 Skill 的系统化实践参考
- [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) — 中文语境下识别和改写 AI 写作痕迹的实践参考
- [blader/humanizer](https://github.com/blader/humanizer) — Claude Code Humanizer skill，系统整理了 AI 痕迹识别和自然化改写思路

感谢 Claude Code、OpenAI Codex 和 DeepSeek 在论文写作辅助和代码生成方面的支持。

## 许可证

[MIT License](LICENSE)
