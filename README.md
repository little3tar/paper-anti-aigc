# Paper Anti-AIGC

一套面向中文工程类毕业论文的 AI 辅助写作工作流与 Skills，根据自己对于论文写作的理解，在 Codex 的帮助下创建，并参考成型项目优化，覆盖任务书解析、大纲规划、证据驱动章节撰写、来源审计、正文润色到格式收尾六个阶段。支持 Claude Code 等兼容 `SKILL.md` 的工具。

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
├── project-ledger.md          ← 项目台账（已确认事实、公式、来源、决策、图表、章节状态）
├── main-tex-context.md        ← 论文主文件结构地图（章节标题、引用方案、模板、关键参数表）
├── materials-inventory.md     ← 用户材料编目清单
├── literature-notes.md        ← 文献笔记临时缓存（写作创建，审计通过后清空）
├── figure-data-manifest.md    ← 图表数据溯源清单（数据文件、生成脚本、输出格式）
├── calculation-records.md     ← 计算底稿（公式代入、参数来源、标准选型、状态）
├── status.json                ← 门控状态（p0_count、p1_count、next_allowed）
│
├── 01-outline.md              ← 阶段 1：大纲 + 文献池 + 图表计划 + 证据需求判断
├── 02-chapter-draft.md        ← 阶段 2：章节细纲 + 证据表 + 正文草稿 + 图表占位符 + 证据缺口清单
├── 03-reference-audit.md      ← 阶段 3：审计报告（P0/P1 分类、公式可复现性、来源一致性）
├── 04-humanized.md            ← 阶段 4：润色稿（降 AI 腔后）
├── 05-format-cleaned.md       ← 阶段 5：格式清理稿（引用位置、命令保护、残留标记清除）
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
├── ledger/                    ← （可选）项目台账拆分为独立文件
│   ├── facts.md               ←   已确认任务要求、约束、术语
│   ├── formulas.md            ←   已确认公式、符号定义、推导说明
│   ├── sources.md             ←   文献来源及 source marker
│   ├── decisions.md           ←   用户确认的大纲、术语、输出格式等决策
│   ├── figures-tables.md      ←   图表占位符、所需数据、生成状态
│   └── chapter-status.md      ←   各章节在各阶段的完成状态
│
├── backups/                   ← 主文件备份（普通备份保留最近 5 个，锚点备份不限）
└── validation/                ← workflow 验证产物（仅验证模式使用）
```

### 各文件/目录说明

#### 项目台账（project-ledger.md）

贯穿全流程的持久化记录，各阶段启动前读取、结束后更新。

| 分区 | 记录内容 | 关键字段 |
| --- | --- | --- |
| `facts` | 已确认任务要求、研究对象、约束条件、术语 | ID、Fact、Type、Source、Status |
| `formulas` | 已确认公式、符号定义、假设、推导说明 | ID、Formula、Purpose、Symbols、Source |
| `sources` | Zotero/本地/网络/用户来源及 source marker | Marker、Title、Authors/Year、Source type、Used in |
| `decisions` | 大纲选择、术语选择、输出格式等用户确认决策 | Date、Decision、Reason、Scope |
| `figures-tables` | 图表占位符、所需数据、生成状态 | ID、Placeholder、Needed content、Source/data、Status |
| `chapter-status` | 各章在各阶段的完成状态 | Chapter、Outline、Evidence、Draft、Audit、Humanize、Format |

状态标签：`confirmed`、`draft`、`needs-source`、`needs-user-data`、`derived`、`superseded`。

#### 阶段产物（01-05）

| 文件 | 产生阶段 | 内容 | 更新时机 |
| --- | --- | --- | --- |
| `01-outline.md` | thesis-outline-planner | 任务理解、文献池、总章节规划、任务-章节映射、图表计划、证据需求判断 | 大纲确认后 |
| `02-chapter-draft.md` | evidence-grounded-chapter-writer | 章节细纲、证据表、公式与参数计划、正文草稿、图表占位符清单、证据缺口清单 | 每章草稿完成后 |
| `03-reference-audit.md` | reference-integrity-auditor | P0/P1 分类、source marker 一致性、公式可复现性审计、来源可靠性评估 | 审计完成后 |
| `04-humanized.md` | engineering-paper-humanizer | 降 AI 腔润色后的正文 | 润色完成后 |
| `05-format-cleaned.md` | academic-format-cleaner | 引用位置修正、命令保护、数学块清理、残留标记清除 | 格式清理完成后 |

#### 工作辅助文件

| 文件 | 用途 | 生命周期 |
| --- | --- | --- |
| `literature-notes.md` | Zotero 文献笔记/标注分批缓存，写作和审计阶段引用 | 写作创建 → 审计校验 → 审计通过后清空 |
| `figure-data-manifest.md` | 图表级数据溯源：数据文件路径、真实/mock、生成脚本、输出格式 | 大纲建框架 → 写作填充 → 审计校验；持久保留 |
| `calculation-records.md` | 计算底稿：公式、代入过程、参数来源、标准选型、状态 | 写作创建 → 审计校验 → 参数变更时标 superseded 追加新行 |

#### status.json（门控）

```json
{
  "p0_count": 0,
  "p1_count": 0,
  "next_allowed": "humanizer"
}
```

- `next_allowed` 取值：`"fix-evidence"` / `"humanizer"` / `"format-cleaner"` / `"next-chapter"`
- P0/P1 > 0 时，`next_allowed` 强制为 `"fix-evidence"`，humanizer 和 format-cleaner **硬性阻断**
- 前一章未完成 humanizer+format-cleaner 时，**禁止开始下一章**

#### evidence/（用户材料）

用户提供的任务书、参考资料、数据、图纸、导师批注等，按类型分目录存放。同名冲突附加时间戳区分；二进制文件直接移动，文本文件统一转 UTF-8。

所有材料在 `materials-inventory.md` 中编目：

| ID | 文件名 | 类型 | 路径 | 提取的关键信息 | 适用章节 | 消化方式 |
| --- | --- | --- | --- | --- | --- | --- |
| M01 | task-book.pdf | 任务书 | evidence/task-book/ | 设计目标、约束 | 全文 | 规划输入 |
| M02 | motor-datasheet.pdf | 数据表 | reference-materials/ | 额定 15kW | §2.3 | 待查外部源 |

> 用户材料仅供内部参考，**不作为正式引用进入正文**。正文中不得出现 `[用户材料: ...]` 或 `[Mxx]` 标记。

`zotero-export/` 存放从 Zotero 导出的 `.bib` 文件，作为审计阶段校验文献信息（题名、作者、年份）准确性的基准。

#### backups/

修改论文主文件前由 `git_snapshot.py` 自动创建。优先使用 Git 分支备份，回退到文件复制备份。普通备份保留最近 5 个（可配置），锚点备份（`--anchor`）永不自动淘汰。

#### ledger/（可选拆分）

当项目规模较大时，`project-ledger.md` 可按分区拆分为 `ledger/` 下的独立文件，便于并行章节各自读写。

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
