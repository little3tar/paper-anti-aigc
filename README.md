<div align="center">

# Paper Anti-AIGC

**中文工程类论文写作、证据审计、润色与格式清理 Skills**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3](https://img.shields.io/badge/Python-≥3.7-green.svg)](https://www.python.org/)
[![Skills](https://img.shields.io/badge/Skills-6-brightgreen.svg)](#已收录-skills)
[![Workflow](https://img.shields.io/badge/Workflow-thesis--writing-orange.svg)](#推荐工作流)
[![Zotero](https://img.shields.io/badge/Zotero-MCP-CC2936.svg)](#文献管理建议)

</div>

---

写论文过程中积累的 Skills 和辅助脚本，配合支持 `SKILL.md` 的 AI 编码工具使用。当前仓库既包含中文工程论文正文润色和格式检查，也包含毕业论文从任务书、大纲、章节草稿、证据审计到后处理的完整 workflow。

> 声明：本项目仅供学术写作组织、证据核验、表达润色和格式自检参考。请遵守所在学校或机构的学术诚信规范，不要使用这些 skills 编造数据、文献、实验结果或标准依据。

## 项目定位

| 目标 | 做法 |
| --- | --- |
| 让论文写作可追踪 | 使用 `.thesis-workflow/` 保存大纲、草稿、审计、润色稿、格式清理稿和 project ledger。 |
| 让正文更像工程论文 | 降低模板化 AI 腔，保留参数、公式、结论和 citation 边界。 |
| 让证据先于润色 | P0/P1 证据问题未处理前，不把缺来源内容润色成定论。 |
| 让格式收尾更稳 | 最后处理 LaTeX/Markdown/plain text 的引用位置、命令保护和残留占位符。 |

## 快速导航

- [已收录 Skills](#已收录-skills)
- [推荐工作流](#推荐工作流)
- [输出与证据原则](#输出与证据原则)
- [文献管理建议](#文献管理建议)
- [安装](#安装)
- [辅助脚本](#辅助脚本)
- [运行产物位置](#运行产物位置)
- [Codex 辅助说明](#codex-辅助说明)
- [致谢](#致谢)

## 已收录 Skills

| Skill | 说明 | 典型场景 | 主要依赖 |
| --- | --- | --- | --- |
| [thesis-writing-workflow](./thesis-writing-workflow/) | 路由完整或局部论文流程，管理确认点、输出格式、主文件、备份、project ledger 和多 skill 协作 | 从任务书到最终清理；或只执行“审计+润色”等局部流程 | 无 |
| [thesis-outline-planner](./thesis-outline-planner/) | 从任务书、设计说明、导师要求生成证据驱动的大纲、文献池、标准规范需求和图表计划 | 开题后规划总章节、任务到章节映射、资料检索计划 | 无 |
| [evidence-grounded-chapter-writer](./evidence-grounded-chapter-writer/) | 基于已确认大纲和证据撰写、扩写或修订章节，维护 source marker、公式/参数计划和证据缺口 | 写某一章、某一节、计算段或设计说明 | 无 |
| [reference-integrity-auditor](./reference-integrity-auditor/) | 审计 unsupported claims、P0/P1、source marker、标准规范来源、公式和计算可复现性 | 润色前审查草稿是否有证据支撑 | 无 |
| [engineering-paper-humanizer](./engineering-paper-humanizer/) | 润色中文工程类论文正文，降低 AI 腔，处理中文标点、引号和破折号 | 证据可靠后的正文润色 | Python ≥3.7 |
| [academic-format-cleaner](./academic-format-cleaner/) | 检查 LaTeX/Markdown/plain text 格式层问题，保护命令、引用、数学块和残留工作标记 | 最终格式清理、LaTeX 报错、引用位置检查 | Python ≥3.7 |

## 推荐工作流

完整流程：

1. `thesis-outline-planner`：规划总大纲、资料池、标准规范和用户材料需求。
2. `evidence-grounded-chapter-writer`：写章节草稿，保留 source marker、公式计划和证据缺口。
3. `reference-integrity-auditor`：审计来源支撑、P0/P1、标准规范、公式和计算链。
4. `engineering-paper-humanizer`：在证据可靠后润色正文。
5. `academic-format-cleaner`：最后做 LaTeX/Markdown/plain text 格式清理。

也可以局部执行，不必每次从第一步开始。例如：

- 只有任务书：用 `thesis-outline-planner`。
- 已有草稿：直接用 `reference-integrity-auditor`。
- 已审计通过的段落：直接用 `engineering-paper-humanizer`。
- 已定稿文本：直接用 `academic-format-cleaner`。
- 组合任务：用 `thesis-writing-workflow` 路由“审计并润色”“润色并格式清理”“写第 3 章并审计”。

```text
任务书/题目
    ↓
thesis-outline-planner
    ↓
evidence-grounded-chapter-writer
    ↓
reference-integrity-auditor
    ↓
engineering-paper-humanizer
    ↓
academic-format-cleaner
```

## 输出与证据原则

- 独立一次性问答未指定时默认在对话中输出 Markdown；真实论文 workflow 中默认主动创建或更新 `.thesis-workflow/` 运行产物。
- 即使只运行其中一个 thesis skill，只要当前目录、用户指定目录或已识别的论文项目根目录中存在 `.thesis-workflow/`，或用户明确处于论文 workflow 项目中，该 skill 结束时也应更新对应阶段产物和必要的 `project-ledger.md`。
- 大纲、章节细纲、P0/P1 证据处理方案和直接修改真实论文主文件需要用户确认；运行产物落盘和更新不等同于内容确认。
- 用户要求生成文件但未指定目录时，默认写入论文项目根目录下的 `.thesis-workflow/`；如果当前目录是 skill 仓库，不能把论文运行产物写进 skill 仓库。
- 用户要求生成文件但未指定拆分方式时，主要内容写入 `.thesis-workflow/` 内的一个默认主文件。
- 论文真实主文件优先使用用户提供或项目中可明确识别的现有主文件名；无法判断时先确认，最后仍无要求时再按格式使用 `main.tex`、`main.docx` 或 `main.md`。
- 每次直接修改用户论文主文件前先备份，并在交付中说明备份路径；修改后即使已写回主文件，也要把本轮结果另存到 `.thesis-workflow/` 对应阶段产物。
- `.thesis-workflow/` 内运行产物默认主动更新，但不对每次更新创建备份；重要确认版、主文件结构大改、用户原始材料变更和真实主文件修改才创建备份或快照。
- 后续章节需要用户自制材料时，例如图纸、结构尺寸、实验记录、仿真截图、程序输出、设备选型依据、现场照片或导师批注，应向用户请求对应内容。
- 行业标准、国家标准、规范、规程、验收要求和限值可作为正式论文依据。核验标准名称、标准号、版本/年份和适用范围后，应融入正文并配正式引用；未核验前只能放入证据缺口。

## 文献管理建议

推荐安装 [Zotero](https://www.zotero.org/) 作为论文文献库，并在支持 MCP 的客户端中配置 [cookjohn/zotero-mcp](https://github.com/cookjohn/zotero-mcp)。该项目提供 Zotero 插件和 MCP 服务能力，可让 AI 助手检索本地 Zotero 文献库、读取元数据、全文、笔记和标注，用于 workflow 中的 Zotero-first 文献检索。

如果 Zotero MCP 不可用，workflow 会退回到本地 `.bib`、`.ris`、`.csv`、PDF 文件夹、用户材料和可靠网络来源；但真实论文写作仍应优先使用用户自己的文献库和已核验来源。

## 安装

将需要的 skill 目录复制到你的 AI 编码工具对应路径。完整 thesis workflow 建议复制全部 6 个目录。

```bash
# OpenCode
cp -r thesis-writing-workflow/ your-project/.opencode/skills/
cp -r thesis-outline-planner/ your-project/.opencode/skills/
cp -r evidence-grounded-chapter-writer/ your-project/.opencode/skills/
cp -r reference-integrity-auditor/ your-project/.opencode/skills/
cp -r engineering-paper-humanizer/ your-project/.opencode/skills/
cp -r academic-format-cleaner/ your-project/.opencode/skills/

# Claude Code / Cursor / other SKILL.md-compatible tools
cp -r thesis-writing-workflow/ your-project/.agents/skills/
cp -r thesis-outline-planner/ your-project/.agents/skills/
cp -r evidence-grounded-chapter-writer/ your-project/.agents/skills/
cp -r reference-integrity-auditor/ your-project/.agents/skills/
cp -r engineering-paper-humanizer/ your-project/.agents/skills/
cp -r academic-format-cleaner/ your-project/.agents/skills/
```

## 辅助脚本

这些脚本只使用 Python 标准库。

```bash
# 中文正文 AI 腔和通用标点检查
python engineering-paper-humanizer/scripts/check_text.py your-paper.tex
python engineering-paper-humanizer/scripts/check_text.py your-doc.md --format markdown
python engineering-paper-humanizer/scripts/check_text.py your-text.txt --format plain

# LaTeX/Markdown/plain text 格式检查
python academic-format-cleaner/scripts/check_format.py your-paper.tex
python academic-format-cleaner/scripts/check_format.py your-doc.md --format markdown
python academic-format-cleaner/scripts/check_format.py your-text.txt --format plain

# 生成规则速查表
python engineering-paper-humanizer/scripts/generate_dict.py
python academic-format-cleaner/scripts/generate_format_dict.py

# 智能备份辅助脚本
python engineering-paper-humanizer/scripts/git_snapshot.py your-paper.tex
python engineering-paper-humanizer/scripts/git_snapshot.py --list
```

`git_snapshot.py` 在已有 Git 仓库且存在提交时优先使用 Git 分支备份；在非 Git 目录、空仓库或 Git 不可用时使用 `.thesis-workflow/backups/` 文件复制备份。脚本不会自动执行 `git init`。

## 运行产物位置

真实论文 workflow 默认使用论文项目根目录下的 `.thesis-workflow/` 保存运行产物：

```text
.thesis-workflow/
├── project-ledger.md
├── main-tex-context.md
├── 01-outline.md
├── 02-chapter-draft.md
├── 03-reference-audit.md
├── 04-humanized.md
├── 05-format-cleaned.md
├── evidence/
├── backups/
└── validation/
```

`main-tex-context.md` 是由 `engineering-paper-humanizer/assets/main-tex-context-template.md` 派生的项目本地上下文文件，应放在 `.thesis-workflow/`，不要写入 skill 目录。

这些运行产物属于论文项目，不属于 skills 仓库。`tests/`、`evals/` 是 skills 仓库维护用，用于检查脚本、规则和 skill 触发边界，不参与论文项目运行，也不应复制到论文项目的 `.thesis-workflow/` 中。

## Codex 辅助说明

本仓库的 workflow 规则整理、skills 拆分、README 结构调整、测试补充和提交历史整理使用了 Codex 工具辅助完成。Codex 在这里主要承担工程化协作角色：

- 根据已有 skill 内容和用户反馈整理可复用工作流规则。
- 辅助维护 `SKILL.md`、README、测试和 eval 说明的一致性。
- 运行本地测试，检查脚本和规则修改后的基础回归。
- 辅助整理 Git 提交历史，便于按阶段阅读仓库演进。

所有论文写作相关输出仍需要用户自行核验事实、来源、数据、公式和学校格式要求。Codex 辅助不替代学术判断、导师意见或正式查重/审稿流程。

## 测试

`tests/` 用于脚本和规则回归测试，`evals/` 用于 skill 触发边界检查。它们只服务于本 skills 仓库维护，不参与论文项目运行。

脚本只依赖 Python 标准库。修改规则或脚本后建议运行：

```bash
python -m unittest discover -s tests
```

## 目录结构

```text
thesis-writing-workflow/
├── SKILL.md
├── agents/openai.yaml
└── references/

thesis-outline-planner/
├── SKILL.md
├── agents/openai.yaml
└── references/

evidence-grounded-chapter-writer/
├── SKILL.md
├── agents/openai.yaml
└── references/

reference-integrity-auditor/
├── SKILL.md
├── agents/openai.yaml
└── references/

engineering-paper-humanizer/
├── SKILL.md
├── agents/openai.yaml
├── assets/
├── references/
└── scripts/

academic-format-cleaner/
├── SKILL.md
├── agents/openai.yaml
├── references/
└── scripts/
```

## 致谢

本仓库中的 `engineering-paper-humanizer` 受以下开源项目启发，并在其基础上针对中文工程论文、证据边界、公式参数保护和论文 workflow 做了本地化扩展：

- [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh)：Humanizer 的中文适配版本，提供了中文语境下识别和改写 AI 写作痕迹的实践参考。
- [blader/humanizer](https://github.com/blader/humanizer)：面向 Claude Code 的 Humanizer skill，系统整理了 AI 写作痕迹识别、二次审计和自然化改写思路。

感谢这些项目对“降低 AI 痕迹不等于规避学术责任，而是让文本回到具体、真实、可核验表达”的启发。本仓库继续沿用这一方向，但把重点放在中文工程类毕业论文中的证据审计、参数保护、工作流追踪和格式收尾。

## 许可证

[MIT License](LICENSE)
