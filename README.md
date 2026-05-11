<div align="center">

# Paper Anti-AIGC

**中文工程类论文写作 · 证据审计 · 去 AI 润色 · 格式清理**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3](https://img.shields.io/badge/Python-%E2%89%A53.7-green.svg)](https://www.python.org/)
[![Skills](https://img.shields.io/badge/Skills-6-brightgreen.svg)](#skills)
[![Workflow](https://img.shields.io/badge/Workflow-thesis--writing-orange.svg)](#workflow)
[![Zotero](https://img.shields.io/badge/Zotero-MCP-CC2936.svg)](#文献管理)

</div>

---

配合支持 `SKILL.md` 的 AI 编码工具使用的论文写作 Skills，覆盖从任务书、大纲规划、章节撰写、证据审计、正文润色到格式收尾的完整工作流。

> **声明**：本项目仅供学术写作组织、证据核验、表达润色和格式自检参考。请遵守所在学校或机构的学术诚信规范，不要使用这些 skills 编造数据、文献、实验结果或标准依据。

## 定位

| 目标 | 做法 |
| --- | --- |
| 论文写作可追踪 | `.thesis-workflow/` 保存大纲、草稿、审计、润色稿、格式清理稿和 project ledger |
| 正文像工程论文 | 降低模板化 AI 腔，保留参数、公式、结论和 citation 边界 |
| 证据先于润色 | P0/P1 证据问题未处理前，不把缺来源内容润色成定论 |
| 格式收尾更稳 | 最后处理 LaTeX/Markdown/plain text 的引用位置、命令保护和残留占位符 |

## Skills

| Skill | 说明 | 场景 | 依赖 |
| --- | --- | --- | --- |
| **[thesis-writing-workflow](./thesis-writing-workflow/)** | 论文流程路由器，管理确认点、输出格式、主文件、备份和多 skill 协作 | 完整流程或局部组合（如"审计+润色"） | — |
| **[thesis-outline-planner](./thesis-outline-planner/)** | 从任务书生成证据驱动的大纲、文献池、标准规范需求和图表计划 | 开题后规划总章节、任务到章节映射 | — |
| **[evidence-grounded-chapter-writer](./evidence-grounded-chapter-writer/)** | 基于大纲和证据撰写章节，维护 source marker、公式计划和证据缺口 | 写某一章/节/计算段/设计说明 | — |
| **[reference-integrity-auditor](./reference-integrity-auditor/)** | 审计 unsupported claims、P0/P1、source marker、标准规范来源、公式可复现性 | 润色前审查证据支撑 | — |
| **[engineering-paper-humanizer](./engineering-paper-humanizer/)** | 润色中文工程论文正文，降 AI 腔，处理中文标点和破折号 | 证据可靠后的正文润色 | Python ≥3.7 |
| **[academic-format-cleaner](./academic-format-cleaner/)** | 格式层检查：引用位置、命令保护、数学块和残留工作标记 | 最终格式清理、LaTeX 报错 | Python ≥3.7 |

## 工作流

```
任务书/题目
    │
    ▼
thesis-outline-planner      ← 大纲、文献池、图表计划
    │
    ▼
evidence-grounded-chapter-writer  ← 章节草稿 + 证据标记
    │
    ▼
reference-integrity-auditor ← 证据审计、P0/P1 分类
    │
    ▼
engineering-paper-humanizer ← 降 AI 腔、润色正文
    │
    ▼
academic-format-cleaner     ← 格式收尾、引用位置清理
```

也可以从中间任意一步进入，不必每次从头开始：

| 如果你有…… | 直接用…… |
| --- | --- |
| 任务书、导师要求 | `thesis-outline-planner` |
| 已有草稿 | `reference-integrity-auditor` |
| 已审计通过的段落 | `engineering-paper-humanizer` |
| 已定稿文本 | `academic-format-cleaner` |
| 组合任务 | `thesis-writing-workflow` 路由 |

## 输出规则

**文件落盘**

- 独立一次性问答默认在对话中输出 Markdown。
- 真实论文 workflow 中默认主动创建或更新 `.thesis-workflow/` 运行产物。
- 生成文件未指定目录时写入论文项目根目录的 `.thesis-workflow/`，不写入 skill 仓库。

**确认门**

- 大纲、章节细纲、P0/P1 处理方案和直接修改论文主文件需要用户确认。
- 运行产物落盘不等同于内容确认。

**备份与安全**

- 直接修改论文主文件前先备份到 `.thesis-workflow/backups/`。
- `.thesis-workflow/` 内运行产物默认主动更新，重要确认版才创建快照。

**证据原则**

- Unsupported facts、parameters、formulas 和 conclusions 不进入正文。
- 行业标准、国家标准、规范、规程须核验名称、标准号、版本/年份和适用范围后，方可作为正式论文依据。
- 后续章节需要用户自制材料（图纸、实验记录、仿真截图、选型依据等）时，应向用户请求。

## 文献管理

推荐 [Zotero](https://www.zotero.org/) + [cookjohn/zotero-mcp](https://github.com/cookjohn/zotero-mcp)，让 AI 助手检索本地文献库的元数据、全文、笔记和标注。

Zotero MCP 不可用时，workflow 退回到 `.bib`、`.ris`、`.csv`、PDF 文件夹和可靠网络来源。

## 安装

将需要的 skill 目录复制到 AI 编码工具的 skills 路径。完整 workflow 建议复制全部 6 个目录。

**OpenCode**

```bash
for skill in thesis-writing-workflow thesis-outline-planner \
  evidence-grounded-chapter-writer reference-integrity-auditor \
  engineering-paper-humanizer academic-format-cleaner; do
  cp -r $skill your-project/.opencode/skills/
done
```

**Claude Code / Cursor / 其他**

```bash
for skill in thesis-writing-workflow thesis-outline-planner \
  evidence-grounded-chapter-writer reference-integrity-auditor \
  engineering-paper-humanizer academic-format-cleaner; do
  cp -r $skill your-project/.agents/skills/
done
```

## 脚本

全部脚本只依赖 Python 标准库（≥3.7）。

### 正文检查（降 AI 腔 + 中文标点）

```bash
python engineering-paper-humanizer/scripts/check_text.py paper.tex
python engineering-paper-humanizer/scripts/check_text.py draft.md   --format markdown
python engineering-paper-humanizer/scripts/check_text.py notes.txt  --format plain
```

### 格式检查（引用位置 + LaTeX 命令 + 残留标记）

```bash
python academic-format-cleaner/scripts/check_format.py paper.tex
python academic-format-cleaner/scripts/check_format.py draft.md   --format markdown
python academic-format-cleaner/scripts/check_format.py notes.txt  --format plain
```

### 规则速查表

```bash
python engineering-paper-humanizer/scripts/generate_dict.py        # AI 腔规则（→ dict.md）
python academic-format-cleaner/scripts/generate_format_dict.py     # 格式规则（→ format-dict.md）
```

两个脚本从 `text_rules.json` / `format_rules.json` 生成人类可读的 Markdown 速查表，用于快速翻阅规则和替换建议。

### 智能备份

```bash
python engineering-paper-humanizer/scripts/git_snapshot.py paper.tex
python engineering-paper-humanizer/scripts/git_snapshot.py --list
python engineering-paper-humanizer/scripts/git_snapshot.py --diff  paper.tex
```

已有 Git 仓库时用分支备份，否则用 `.thesis-workflow/backups/` 文件复制。不自动执行 `git init`。

## 运行产物

真实论文 workflow 默认使用论文项目根目录下的 `.thesis-workflow/`：

```text
.thesis-workflow/
├── project-ledger.md          ← 已确认事实、公式、来源、决策
├── main-tex-context.md        ← 论文主文件结构地图
├── 01-outline.md              ← 大纲 + 文献池
├── 02-chapter-draft.md        ← 章节草稿 + 证据表
├── 03-reference-audit.md      ← 审计报告
├── 04-humanized.md            ← 润色稿
├── 05-format-cleaned.md       ← 格式清理稿
├── evidence/                  ← 用户材料 & 文献
├── backups/                   ← 主文件备份
└── validation/                ← workflow 验证产物
```

> `tests/` 和 `evals/` 仅供 skills 仓库维护用，不参与论文运行。

## 测试

```bash
python -m unittest discover -s tests
```

`tests/` 用于脚本和规则回归，`evals/` 用于 skill 触发边界检查。修改规则或脚本后建议运行。

## 致谢

`engineering-paper-humanizer` 受以下项目启发，并针对中文工程论文、证据边界、公式参数保护和论文 workflow 做了本地化扩展：

- [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) — 中文语境下识别和改写 AI 写作痕迹的实践参考
- [blader/humanizer](https://github.com/blader/humanizer) — Claude Code Humanizer skill，系统整理了 AI 痕迹识别和自然化改写思路

核心理念：降 AI 痕迹不等于规避学术责任，而是让文本回到具体、真实、可核验的表达。

## 许可证

[MIT License](LICENSE)
