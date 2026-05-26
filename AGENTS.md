# 论文工作流 Skills 仓库

一套中文工程类毕业论文 AI 辅助写作工作流。**本仓库是 skills 维护项目**，不是论文项目本身——论文产物写入用户项目的 `.thesis-workflow/`。

## 组件

| 目录 | 用途 |
|---|---|
| `skills/` | 7 个 skill（6 个论文工作流 + 1 个 docx 翻译），渐进式加载（SKILL.md + references/ + scripts/） |
| `hooks/` | SessionStart 钩子（注入工作流状态到新会话）+ PreToolUse 钩子（四道防线：主文件保护、阶段门控、跳阶段确认、细纲确认阻塞） |
| `tests/` | 脚本回归测试，不参与论文项目运行 |
| `evals/` | skill description 触发边界评估，不参与论文项目运行 |

skills 架构：`thesis-writing-workflow`（路由器）→ `thesis-outline-planner` → `evidence-grounded-chapter-writer` → `reference-integrity-auditor` → `engineering-paper-humanizer` → `academic-format-cleaner`。

## 编写约束

### 单一权威定义
每条规则只在一处完整定义，他处一句话引用。以下规则已有权威定义，不在其他文件中完整重述：

| 规则 | 权威位置 |
|---|---|
| A/B/C 分类 | `skills/thesis-writing-workflow/references/user-material-protocol.md` |
| Zotero 笔记协议 | `skills/evidence-grounded-chapter-writer/references/literature-notes-cache-rules.md` |
| source marker 格式 | `skills/evidence-grounded-chapter-writer/references/citation-key-rules.md` |
| 备份协议 | `skills/thesis-writing-workflow/references/output-and-backup.md` §备份协议 |
| 输出与文件安全（产物路径、更新规则） | `skills/thesis-writing-workflow/references/output-and-backup.md` §输出规则 |
| 门控逻辑（各阶段准入条件） | workflow §强制串行规则 |
| 执行模式语义（Review-gated / Preauthorized / Validation / 工作流vs独立） | workflow §执行模式 |
| 阶段入口条件（前置条件 + 阻塞条件） | workflow §阶段输入契约 |
| 修改回环（分级/产物更新/备份） | `skills/thesis-writing-workflow/references/revision-loop.md` |
| 项目台账规则（结构/标签/存放位置） | `skills/thesis-writing-workflow/references/project-ledger-rules.md` |
| 三级来源检索协议（Zotero → 用户 → 网络） | `skills/thesis-writing-workflow/references/source-policy.md` |
| 主文件上下文模板（格式约定字段） | `skills/thesis-writing-workflow/references/main-tex-context-template.md` |
| 图表数据溯源规则（Figure ID、数据文件、生成脚本、状态） | `skills/evidence-grounded-chapter-writer/references/figure-data-manifest-rules.md` |

### 不描述默认行为
只写例外。持久文件不写"保留不删除"，正常备份不写"保留最近 N 个"。

### Red Flag = 反直觉的 AI 陷阱
只放 AI 特有的直觉错误。不是规则重述。写之前问：这是 AI 才容易犯的错吗？

### ⭐ 标记约定

`⭐` 标记表示"AI 容易跳过或遗漏的强制步骤"——不标 ⭐ 的步骤 AI 可能因对话压缩、上下文丢失或直觉判断而省略。仅用于真实存在的 AI 遗漏模式，不用作通用强调。

### 中文排版

技术文档自身的中文正文使用弯引号 `""`、`''`，代码块和 YAML frontmatter 中的字符串使用 ASCII 直引号。

### 子 skill 引用 workflow，不复述
文件产出 boilerplate 只在 workflow §输出与文件安全 定义。子 skill 步骤 1 写："文件产出规则遵循 workflow §输出与文件安全。本阶段产物为 `.thesis-workflow/chapters/chX/xxx.md`。"

### 跨 skill 引用可解析

用文字说明（"见 workflow router 的同名参考文件"），不写 `../other-skill/references/xxx.md`。

子 skill 参考文件表中的跨 skill 引用统一使用"见 <skill> 参考文件 `xxx.md`"格式，用途列填写该文件在本 skill 中的使用场景。

### 脚本自包含

每个 skill 的 `scripts/` 不跨 skill 导入代码。如需共享工具函数，在各 skill 的 `scripts/` 下维护独立副本（如 `_shared.py`），每个副本只包含该 skill 实际使用的函数，确保每个 skill 可独立部署。

修改共享函数时，只更新使用了该函数的 skill 副本，不同步到不使用该函数的 skill。当前分布：`git_snapshot.py`（workflow 含全部命令，humanizer 和 format-cleaner 仅含 `cmd_snapshot` 备份入口）、`_shared.py`（workflow 仅含 `setup_windows_utf8`，humanizer 版额外含 `mask_latex_inline_protected` 等函数，format-cleaner 版不含 humanizer 专有函数）。

### 新增产物同步
新增 `.thesis-workflow/` 产物 → 同步更新 `README.md` 目录树 + 产物表、`workflow SKILL.md` 产出物列表。新增 `chapters/chX/` 下的阶段产物 → 同步更新目录树。新增 reference 文件 → 在所属 skill 参考文件表追加一行，并同步本文件（AGENTS.md）的单一权威定义表。

### 修改前先研究
修改 skills 或 hooks 前，必须通过 skill-creator 和联网搜索获取相关知识——skill 设计最佳实践、相似问题的解决模式、AI 指令执行的已知陷阱。禁止凭直觉直接改，先研究再动手。

## 新用户引导

当用户表达论文写作意图但未指定具体阶段时，按顺序引导，不假定用户了解工作流：

1. **确认输入**：询问用户是否有任务书、设计说明、导师要求或论文题目。
2. **确认输出**：询问输出格式（Markdown/LaTeX/纯文本）和主文件位置。未指定时默认 Markdown + `output/` 子目录。
3. **选择入口**：
   - 有任务书/题目 → 从大纲规划开始
   - 已有大纲 → 从章节写作开始
   - 已有草稿 → 从证据审计开始
   - 粘贴文字要求润色 → 独立润色模式
   - 不确定 → 从大纲规划开始
4. **切换阶段时简短解释**：告诉用户当前在哪个阶段、产出什么。用中文名称描述，不假设用户知道阶段顺序。
5. **首次使用关键提醒**：草稿不直接写主文件（中间产物在 `.thesis-workflow/`）；每个阶段有确认检查点；有 Zotero 可告知 AI 尝试连接。

### 输出风格

面向用户时用自然中文，避免术语缩写（"调用 skill"→"开始规划大纲"、"触发 workflow"→"启动论文流程"）。首次描述用完整句子，不依赖编号列表。

## Git

提交格式：`type(scope): description`。`improve-workflow` 是当前工作分支。

### 合并策略

工作分支合并到 `main` 时使用 `git merge --no-ff`（非快进合并），不用 squash：

```bash
git checkout main
git merge --no-ff improve-workflow -m "merge: <总结 improve-workflow 本次合并包含的改动>"
```

`--no-ff` 确保始终产生一个双亲 merge commit，分支的提交历史完整保留在 `git log --graph` 中可见。不使用 `--squash`（会压成一次提交丢失分支链），不使用 `reset --hard` 后重新开始（会丢失 reflog 追溯）。
