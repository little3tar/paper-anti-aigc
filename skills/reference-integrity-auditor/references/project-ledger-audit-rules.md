# 项目台账审计规则

当论文项目维护了 `facts.md`、`formulas.md`、`sources.md`、`decisions.md`、`figures-tables.md` 和 `chapter-status.md` 等台账文件时使用本规则。

## 对照台账审计

对照已确认的台账条目检查草稿：

- 草稿中的事实不应与 `facts.md` 矛盾。
- 公式、符号、假设和适用范围应与 `formulas.md` 一致。
- 引用占位符和来源注释应能在 `sources.md` 中解析（当来源已知时）。
- 章节结构和已批准的选择应与 `decisions.md` 一致。
- 图表占位符应与 `figures-tables.md` 匹配，或作为建议更新加入。

## 发现类型

- `ledger-missing`：草稿引入了新的事实、参数、公式或来源，应添加到台账中。
- `ledger-conflict`：草稿与已确认的台账条目不矛盾。
- `ledger-stale`：台账中包含已废弃的值，草稿仍在使用。
- `ledger-unresolved`：草稿依赖标记为 `needs-source` 或 `needs-user-data` 的条目。

## 规则

审计期间不要静默更新已确认的台账条目。报告建议的更改并征求确认，除非用户明确要求直接编辑文件。
