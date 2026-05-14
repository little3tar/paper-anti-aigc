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
```

**OpenCode**

```bash
cp -r skills/* your-project/.opencode/skills/
cp -r hooks/* your-project/.opencode/hooks/
```

**Cursor / 其他**

```bash
cp -r skills/* your-project/.agents/skills/
cp -r hooks/* your-project/.cursorkit/hooks/
```

## 运行产物

真实论文工作流默认使用论文项目根目录下的 `.thesis-workflow/`，各阶段产物说明如下。

### 目录总览

```text
.thesis-workflow/
├── project-ledger.md          ← 台账索引文件（指向 ledger/ 各文件）
├── main-tex-context.md        ← 论文主文件结构地图（引用 ledger/，不复制参数）
├── materials-inventory.md     ← 用户材料编目清单
├── literature-notes.md        ← 文献笔记临时缓存（写作创建，审计通过后清空）
├── literature-pool.md         ← 文献池全表（60条，6组分类，含 ZoteroKey 映射）
├── figure-data-manifest.md    ← 图表数据溯源清单（数据文件、生成脚本、输出格式）
├── calculation-records.md     ← 数值唯一权威源（公式代入、参数来源、标准选型）
├── operations-log.md          ← 操作日志（项目检查、章节清除等一次性操作，只追加）
├── status.json                ← 门控状态（p0_count、p1_count、next_allowed）
│
├── ledger/                    ← 项目台账（拆分后，各子文件独立读写）
│   ├── facts.md               ←   已确认设计参数、引用标准、MC51 公开数据
│   ├── decisions.md           ←   已确认决策（输出格式/路径/引用方案）
│   ├── chapter-status.md      ←   各章 6 阶段完成状态
│   └── questions.md           ←   结构化待确认问题
│
├── outlines/                  ← 章节细纲（段落级写作点，每章一份）
│   └── ch2-detailed.md        ←   第2章细纲
│
├── 01-outline.md              ← 阶段 1：总大纲（章→节→小节）+ 文献池分组摘要
├── 02-chapter-draft.md        ← 阶段 2：章节正文草稿（内容权威源）
├── 03-reference-audit.md      ← 阶段 3：审计报告 + 文献修正记录
├── 04-humanized.md            ← 阶段 4：润色操作记录（非全文副本）
├── 05-format-cleaned.md       ← 阶段 5：格式修复记录（非全文副本）
│
├── evidence/                  ← 用户提供材料的物理存放
│   ├── task-book/             ←   任务书、设计说明、开题报告
│   ├── reference-materials/   ←   用户提供的论文、手册、教材副本
│   ├── user-data/             ←   用户自算数据、实验记录、仿真结果
│   ├── user-figures/          ←   用户自制的图、照片、截图
│   ├── user-code/             ←   用户提供的程序、脚本
│   ├── advisor-notes/         ←   导师批注、会议记录
│   ├── standards-specs/       ←   用户提供的标准规范文件
│   └── zotero-export/         ←   Zotero 导出的 .bib 文件（文献信息校验基准）
│
├── backups/                   ← 主文件备份（普通备份保留最近 5 个，锚点备份不限）
└── validation/                ← workflow 验证产物（仅验证模式使用）
```

### 各文件/目录说明

#### 项目台账（ledger/）

已拆分为 `ledger/` 子目录。索引文件 `project-ledger.md` 指向各子文件。

| 文件 | 记录内容 | 关键字段 |
| --- | --- | --- |
| `ledger/facts.md` | 已确认设计参数、引用标准、MC51公开数据 | 参数、来源、性质(A/B/C)、计算记录ID |
| `ledger/decisions.md` | 输出格式、文件路径、引用方案等用户确认决策 | 日期、决策、理由、影响范围 |
| `ledger/chapter-status.md` | 各章阶段完成状态（6 列：大纲/细纲/草稿/审计/润色/格式） | 章节、大纲、细纲、草稿、审计、润色、格式 |
| `ledger/questions.md` | 结构化待确认问题 | 编号、问题、阻塞章节、优先级、状态 |

**数值单一权威源**：计算类数值（缸径、推力等）只在 `calculation-records.md` 中定义。`ledger/facts.md` 只记录参数名和关联计算记录 ID，不复制数值。

状态标签：`confirmed`、`draft`、`needs-source`、`needs-user-data`、`derived`、`superseded`。

#### 阶段产物（01-05）

| 文件 | 产生阶段 | 内容 | 更新时机 |
| --- | --- | --- | --- |
| `01-outline.md` | thesis-outline-planner | 总大纲（章→节→小节）+ 文献池分组摘要 | 大纲确认后 |
| `literature-pool.md` | thesis-outline-planner | 文献池全表（60条，6组，含 ZoteroKey） | 大纲确认后 |
| `outlines/chX-detailed.md` | evidence-grounded-chapter-writer | 章节细纲（段落级写作点） | 细纲确认后 |
| `02-chapter-draft.md` | evidence-grounded-chapter-writer | 章节正文草稿（内容权威源） | 每章草稿完成后 |
| `03-reference-audit.md` | reference-integrity-auditor | 审计报告 + 文献修正记录 | 审计完成后 |
| `04-humanized.md` | engineering-paper-humanizer | 润色操作记录（非全文副本，最终文本写入 main.md/txt） | 润色完成后 |
| `05-format-cleaned.md` | academic-format-cleaner | 格式修复记录（非全文副本，最终文本写入 main.md/txt） | 格式清理完成后 |
| `operations-log.md` | 各阶段 | 批量操作/项目检查/章节清除记录（只追加） | 批量操作后 |

#### 工作辅助文件

| 文件 | 用途 | 生命周期 |
| --- | --- | --- |
| `literature-notes.md` | Zotero 文献笔记/标注分批缓存，写作和审计阶段引用 | 写作创建 → 审计校验 → 审计通过后清空 |
| `figure-data-manifest.md` | 图表级数据溯源：数据文件路径、真实/mock、生成脚本、输出格式 | 大纲建框架 → 写作填充 → 审计校验；持久保留 |
| `calculation-records.md` | 计算底稿：公式、代入过程、参数来源、标准选型、状态 | 写作创建 → 审计校验 → 参数变更时标 superseded 追加新行 |

#### status.json（门控）

```json
{
  "stage": "audited",
  "timestamp": "2026-05-13T22:00:00",
  "p0_count": 0,
  "p1_count": 0,
  "green_paragraphs": ["§2.1", "§3.2"],
  "blocked_paragraphs": ["§2.3"],
  "next_allowed": "humanizer",
  "notes": ""
}
```

- `stage`：当前所处阶段（`planned` / `written` / `audited` / `humanized` / `format-cleaned`）。`planned` 和 `written` 为信息性标记；门控逻辑主要关注后三个阶段。
- `p0_count` / `p1_count`：P0/P1 问题计数
- `next_allowed` 取值：`"fix-evidence"` / `"humanizer"` / `"format-cleaner"` / `"next-chapter"`
- P0/P1 > 0 时，`next_allowed` 强制为 `"fix-evidence"`，humanizer 和 format-cleaner **硬性阻断**
- 前一章未完成 humanizer+format-cleaner 时，**禁止开始下一章**

#### evidence/（用户材料）

用户提供的任务书、参考资料、数据、图纸、导师批注等，按类型分目录存放。同名冲突附加时间戳区分；二进制文件直接移动，文本文件统一转 UTF-8。

所有材料在 `materials-inventory.md` 中编目：

| ID | 文件名 | 类型 | 路径 | 提取的关键信息 | 数据性质 | 适用章节 | 消化方式 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | task-book.pdf | 任务书 | evidence/task-book/ | 设计目标、约束 | — | 全文 | 规划输入 |
| M02 | motor-datasheet.pdf | 数据表 | reference-materials/ | 额定 15kW | A | §2.3 | 待查外部源 |

> 用户材料仅供内部参考，**不作为正式引用进入正文**。正文中不得出现 `[用户材料: ...]` 或 `[Mxx]` 标记。

`zotero-export/` 存放从 Zotero 导出的 `.bib` 文件，作为审计阶段校验文献信息（题名、作者、年份）准确性的基准。

#### backups/

修改论文主文件前由 `git_snapshot.py` 自动创建。优先使用 Git 分支备份，回退到文件复制备份。普通备份保留最近 5 个（可配置），锚点备份（`--anchor`）永不自动淘汰。

#### ledger/（台账子目录）

`project-ledger.md` 已拆分为 `ledger/` 下的独立文件（facts/decisions/chapter-status/questions），各自独立读写。`project-ledger.md` 为汇总索引。

#### outlines/（章节细纲）

每章的段落级细纲独立存储（`chX-detailed.md`），写作前由 chapter-writer 生成并经用户确认。总大纲 `01-outline.md` 只保留到小节标题层级。

#### literature-pool.md（文献池全表）

从 `01-outline.md` 分离的 60 条文献全表，6 组分类，含 ZoteroKey 映射。大纲中只保留分组摘要。

#### operations-log.md（操作日志）

批量操作、项目检查和重大变更记录。只追加，不修改已有记录。

#### validation/

仅在验证/测试模式下使用，存放合成输入和验证产物，不参与真实论文流程。

## 脚本

全部脚本只依赖 Python 标准库（≥3.7）。

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
python skills/engineering-paper-humanizer/scripts/git_snapshot.py paper.tex
python skills/engineering-paper-humanizer/scripts/git_snapshot.py paper.tex --anchor
python skills/engineering-paper-humanizer/scripts/git_snapshot.py --list
python skills/engineering-paper-humanizer/scripts/git_snapshot.py --rollback paper.tex
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

## 致谢

本项目受以下项目启发：

- [Norman-bury/research-writing-skill](https://github.com/Norman-bury/research-writing-skill) — 研究写作 Skill 的系统化实践参考
- [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) — 中文语境下识别和改写 AI 写作痕迹的实践参考
- [blader/humanizer](https://github.com/blader/humanizer) — Claude Code Humanizer skill，系统整理了 AI 痕迹识别和自然化改写思路

感谢 Claude Code、OpenAI Codex 和 DeepSeek 在论文写作辅助和代码生成方面的支持。

## 许可证

[MIT License](LICENSE)
