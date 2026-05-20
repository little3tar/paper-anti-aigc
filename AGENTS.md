# 论文工作流 Skills 仓库

一套中文工程类毕业论文 AI 辅助写作工作流。**本仓库是 skills 维护项目**，不是论文项目本身——论文产物写入用户项目的 `.thesis-workflow/`。

## 组件

| 目录 | 用途 |
|---|---|
| `skills/` | 6 个论文工作流 skill，渐进式加载（SKILL.md + references/ + scripts/） |
| `hooks/` | SessionStart 钩子（注入工作流状态到新会话）+ PreToolUse 钩子（三道防线：主文件保护、阶段门控、跳阶段确认） |
| `tests/` | 脚本回归测试，不参与论文项目运行 |
| `evals/` | skill description 触发边界评估，不参与论文项目运行 |

skills 架构：`thesis-writing-workflow`（路由器）→ `thesis-outline-planner` → `evidence-grounded-chapter-writer` → `reference-integrity-auditor` → `engineering-paper-humanizer` → `academic-format-cleaner`。

## 编写约束

### 单一权威定义
每条规则只在一处完整定义，他处一句话引用。以下规则已有权威定义，不在其他文件中完整重述：

| 规则 | 权威位置 |
|---|---|
| A/B/C 分类 | `references/user-material-protocol.md` |
| Zotero 笔记协议 | `literature-notes-cache-rules.md` |
| source marker 格式 | `citation-key-rules.md` |
| 备份协议 | workflow §备份协议 |
| 门控逻辑（各阶段准入条件） | workflow §强制串行规则 |
| 执行模式语义（Review-gated / Preauthorized / Validation / 工作流vs独立） | workflow §执行模式 |
| 阶段入口条件（前置条件 + 阻塞条件） | workflow §阶段输入契约 |
| 修改回环（分级/产物更新/备份） | `references/revision-loop.md` |

### 不描述默认行为
只写例外。持久文件不写"保留不删除"，正常备份不写"保留最近 N 个"。

### Red Flag = 反直觉的 AI 陷阱
只放 AI 特有的直觉错误。不是规则重述。写之前问：这是 AI 才容易犯的错吗？

### 子 skill 引用 workflow，不复述
文件产出 boilerplate 只在 workflow §输出与文件安全 定义。子 skill 步骤 1 写："文件产出规则遵循 workflow §输出与文件安全。本阶段产物为 `.thesis-workflow/chapters/chX/xxx.md`。"

### 跨 skill 引用可解析

用文字说明（"见 workflow router 的同名参考文件"），不写 `../other-skill/references/xxx.md`。

### 脚本自包含

每个 skill 的 `scripts/` 不跨 skill 导入代码。如需共享工具函数，在各 skill 的 `scripts/` 下维护独立副本（如 `_shared.py`），确保每个 skill 可独立部署。

### 新增产物同步
新增 `.thesis-workflow/` 产物 → 同步更新 `README.md` 目录树 + 产物表、`workflow SKILL.md` 产出物列表。新增 `chapters/chX/` 下的阶段产物 → 同步更新目录树。新增 reference 文件 → 在所属 skill 参考文件表追加一行，并同步 `AGENTS.md` 和 `CLAUDE.md` 的单一权威定义表。

## Git

提交格式：`type(scope): description`。`improve-workflow` 是当前工作分支。

### 合并策略

工作分支合并到 `main` 时使用 `git merge --no-ff`（非快进合并），不用 squash：

```bash
git checkout main
git merge --no-ff improve-workflow -m "merge: <总结 improve-workflow 本次合并包含的改动>"
```

`--no-ff` 确保始终产生一个双亲 merge commit，分支的提交历史完整保留在 `git log --graph` 中可见。不使用 `--squash`（会压成一次提交丢失分支链），不使用 `reset --hard` 后重新开始（会丢失 reflog 追溯）。合并说明使用中文。
