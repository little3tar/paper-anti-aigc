# 项目台账规则

> 简要引用。完整规则定义见 workflow router 同名参考文件 `project-ledger-rules.md`。

## 写作阶段的台账操作

**起草前**：
- 读取 `ledger/facts.md`，获取已确认的设计参数、材料属性、约束条件
- 读取 `ledger/decisions.md`，获取已确认的选型决策、方案取舍及理由
- 读取 `ledger/chapter-status.md`，了解上下游章节进度和阻塞项
- 读取 `ledger/questions.md`，确认是否有待回答的用户问题影响本章写作

**起草完成后**：
- 新产生的设计参数、实验数据、材料属性 → 追加到 `ledger/facts.md`
- 新做出的选型、方案、取舍决策 → 追加到 `ledger/decisions.md`
- 本章标记为 `drafting` → 更新 `ledger/chapter-status.md`

状态标签定义和完整列规范见 workflow router 同名参考文件。
