# 论文工作流 Skills 仓库

一套中文工程类毕业论文 AI 辅助写作工作流。**本仓库是 skills 维护项目**，不是论文项目本身——论文产物写入用户项目的 `.thesis-workflow/`。

## 组件

| 目录 | 用途 |
|---|---|
| `skills/` | 6 个论文工作流 skill，渐进式加载（SKILL.md + references/ + scripts/） |
| `hooks/` | SessionStart 钩子：检测 `.thesis-workflow/status.json`，自动注入工作流状态到新会话 |
| `tests/` | 脚本回归测试，不参与论文项目运行 |
| `evals/` | skill description 触发边界评估，不参与论文项目运行 |

skills 架构：`thesis-writing-workflow`（路由器）→ `thesis-outline-planner` → `evidence-grounded-chapter-writer` → `reference-integrity-auditor` → `engineering-paper-humanizer` → `academic-format-cleaner`。

## 编写约束

### 单一权威定义
每条规则只在一处完整定义，他处一句话引用。以下规则已有权威定义，不在其他文件中完整重述：A/B/C 分类（workflow）、Zotero 笔记协议（`literature-notes-cache-rules.md`）、source marker 格式（`citation-key-rules.md`）、备份协议（workflow §备份协议）。

### 不描述默认行为
只写例外。持久文件不写"保留不删除"，正常备份不写"保留最近 N 个"。

### Red Flag = 反直觉的 AI 陷阱
只放 AI 特有的直觉错误。不是规则重述。写之前问：这是 AI 才容易犯的错吗？

### 子 skill 引用 workflow，不复述
文件产出 boilerplate 只在 workflow §输出与文件安全 定义。子 skill 步骤 1 写："文件产出规则遵循 workflow §输出与文件安全。本阶段产物为 `.thesis-workflow/XX-xxx.md`。"

### 跨 skill 引用可解析
用文字说明（"见 workflow router 的同名参考文件"），不写 `../other-skill/references/xxx.md`。

### 新增产物同步
新增 `.thesis-workflow/` 产物 → 同步更新 `README.md` 目录树 + 产物表、`workflow SKILL.md` 产出物列表。新增 reference 文件 → 在所属 skill 参考文件表追加一行。

## Git

提交格式：`type(scope): description`。`improve-workflow` 是当前工作分支。
