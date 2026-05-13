# 项目台账规则

规范的 project ledger 结构、状态标签和完整列定义见 workflow router 的同名参考文件 `project-ledger-rules.md`。本章节写作 skill 的 ledger 使用要点如下。

本章节写作 skill 的 ledger 使用要点：

- 起草章节前先读取 `.thesis-workflow/ledger/` 下相关文件（facts/decisions/chapter-status，如存在）。
- 起草完成后，若产生了新的已确认事实、公式、参数、来源、设计决策或证据缺口，应更新 `ledger/` 对应文件。
- 只有保存位置或是否使用文件不明确时才询问用户。
- 未确认项使用 `draft`、`needs-source` 或 `needs-user-data`，不要因为某内容在草稿中有用就将其标记为 `confirmed`。

状态标签：

- `confirmed`
- `draft`
- `needs-source`
- `needs-user-data`
- `derived`
- `superseded`

不要静默覆盖已确认条目。参数、公式或决策变更时保留旧条目并标记 `superseded`。
