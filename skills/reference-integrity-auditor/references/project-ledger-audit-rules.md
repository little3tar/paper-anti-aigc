# 项目台账审计规则

当论文项目维护了 `ledger/` 子目录（`facts.md`、`decisions.md`、`chapter-status.md`、`questions.md`）时使用本规则。台账结构定义见 workflow router 的同名参考文件 `project-ledger-rules.md`。

## 对照台账审计

对照已确认的台账条目检查草稿：

- 草稿中的设计参数不应与 `ledger/facts.md` 矛盾。
- 输出格式、路径、引用方案等决策应与 `ledger/decisions.md` 一致。
- 章节进展状态应与 `ledger/chapter-status.md` 反映的实际进度相符。
- 已确认的设计参数在正文中的表述应与 `ledger/facts.md` 中的性质和来源一致。
- 正文数值应与 `calculation-records.md` 中的对应记录一致（计算记录是数值单一权威源）。

## 发现类型

- `ledger-missing`：草稿引入了新的设计参数或决策，应添加到 `ledger/` 对应文件中。
- `ledger-conflict`：草稿与已确认的台账条目矛盾。
- `ledger-stale`：台账中包含已废弃的值，草稿仍在使用。
- `ledger-unresolved`：草稿依赖标记为 `needs-source` 或 `needs-user-data` 的条目。

## 规则

审计期间不要静默更新已确认的台账条目。报告建议的更改并征求确认，除非用户明确要求直接编辑文件。
