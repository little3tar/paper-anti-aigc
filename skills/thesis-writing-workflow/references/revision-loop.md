# 主文件输出后的修改回环

全流程完成、文本写入主文件后，用户审阅时可能发现需要修改。此时 `status.json` 中 `next_allowed` 为 `"next-chapter"`，PreToolUse 钩子已放行主文件写入。修改后的内容仍须经过润色和格式审核，不得因为"工作流已完成"就直接交付未处理的文本。

写回目标为对应章节文件 `main-chX.md` / `main-chX.txt` / `main-chX.tex`。修改回环规则按章独立适用——改哪章就对该章文件执行备份和分级处理，不波及未修改的章。

## 修改分级与处理路径

收到修改请求后，先判断修改幅度，按对应路径处理。下表中的"主文件"指对应章文件 `main-chX.md`：

| 级别 | 判断标准 | 处理路径 |
|---|---|---|
| **L1 微调** | 错别字、标点修正、单个术语替换、数字勘误 | 直接改主文件，无需重跑阶段。改后运行 `check_text.py` 和 `check_format.py` 确认无新增问题。 |
| **L2 局部重写** | 1-3 个句子重写、段落内结构调整、表述优化 | ① 先改主文件 ② 运行 `check_text.py` 复查 AI 腔指标 ③ 运行 `check_format.py` 复查格式 ④ 若检查未通过 → 对变更段落重跑 humanizer → 再跑 format-cleaner → 更新主文件 |
| **L3 内容变更** | 新增段落、删除段落、数据/结论改动、结构调整 | ① 先改 `chapters/chX/draft.md`（内容权威源必须同步） ② 如变更涉及证据/数据，更新 `calculation-records.md` 和 `ledger/facts.md` ③ 对变更部分重跑 humanizer（阶段 4） ④ 重跑 format-cleaner（阶段 5） ⑤ 将处理后的文本更新到主文件 ⑥ 更新 `ledger/chapter-status.md` 和 `operations-log.md` |

## 修改回环的产物更新

| 修改级别 | 更新 `chapters/chX/draft.md` | 更新 `chapters/chX/humanized.md` | 更新 `chapters/chX/format-cleaned.md` | 重跑检查脚本 |
|---|---|---|---|---|
| L1 | 不需要 | 不需要 | 不需要 | 建议（确认无新增问题） |
| L2 | 不需要 | 追加本轮变更记录 | 追加本轮变更记录 | 必须 |
| L3 | 必须 | 追加本轮变更记录 | 追加本轮变更记录 | 必须 |

## 回环中的备份

备份操作遵循 `output-and-backup.md` §备份协议。回环特有规则：

- L2 / L3 修改前，先通过 `git_snapshot.py <主文件>` 创建备份。
- L3 修改前额外备份 `chapters/chX/draft.md`：`git_snapshot.py .thesis-workflow/chapters/chX/draft.md`。
- 多次回环时，每次修改前均备份，不覆盖之前的备份。

## 禁止事项

- 不得因为"工作流已完成"就将 L2/L3 级修改直接写入主文件而不重跑检查和润色。
- L3 级修改不得只改主文件而不同步 `chapters/chX/draft.md`——草稿是内容权威源，主文件是输出快照。
- 拆分模式下，不得因修改第 X 章而未经检查就同步改动其他章的主文件。
- 回环中不得修改 `status.json` 的 `next_allowed`——该字段由各阶段的正式流程依次更新：审计（`"humanizer"`）→ humanizer（`"format-cleaner"`）→ format-cleaner（`"next-chapter"`）。回环修改不进正式流程，不更新门控状态。
	
	**适用范围**：此规则适用于主文件输出后的用户审阅修改回环（L1/L2/L3 级修改）。**审计修复闭环**（P0/P1 > 0 时的 fix-evidence 循环，见 workflow §审计退回修复闭环）独立管理——该闭环中 auditor 在 P0/P1 清零后必须更新 `next_allowed` 为 `"humanizer"`，不受此限制。
