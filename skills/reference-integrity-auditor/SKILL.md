---
name: reference-integrity-auditor
description: >-
  用于审计中文工程类论文草稿的证据完整性。用户要求审计/检查证据、查引用/来源、
  查有没有缺文献/缺参数、检查公式能不能复现、unsupported claims、weak citations、
  fabricated-looking literature、P0/P1 问题、source marker 一致性、标准规范来源核验时使用。
  应在章节写作之后、润色和格式清理之前运行。
---

# Reference Integrity Auditor

## Red Flags（停止并检查）

| AI的想法 | 正确做法 |
|---|---|
| "只有几个 P2 问题，可以放行" | P0/P1 任一 > 0 必须阻塞下游，status.json 写 `"next_allowed": "fix-evidence"` |
| "引用格式不太对但意思到了" | 标准规范缺版本/年份/发布机构按 P1 处理 |
| "验证模式下不需要严格审计" | 验证模式也须标记所有问题，只在标记后可继续 |
| "status.json 不写也没关系" | 门控文件是 humanizer 和 format-cleaner 的强制检查点 |
| "这个标准是常识，不用核验" | 凡涉及限值、验收、安全裕量的标准必须核验版本和条文 |
| "marker 存在就行，题名对不对不重要" | 须对照 Zotero 库或 `.bib` 导出抽查题名/作者/年份准确性 |
| "文献笔记缓存里有，但获取状态是'无笔记'，我再试一次" | 标记为 `无笔记` 或 `获取失败` 的条目直接跳过，不重试。笔记缺失不自动升级为 P0/P1 |
| "这个 claim 缺来源，Zotero 没找到，标记 P1 就行" | 缺来源时必须按三级检索协议（Zotero → 用户 → Web）依次尝试补全，每项都要尝试。只有三级都未获取的才能标记为 P1 并列入证据缺口 |

本 skill 用来检查论文大纲、章节草稿或小节草稿是否真的被来源支撑。它应在风格润色之前运行，避免文本变得更流畅但证据仍然薄弱。

## 审计模式

- **Submission mode**：真实提交或定稿前使用。只要仍有 P0/P1 问题，就停止下游润色和格式收尾。
- **Validation mode**：测试 workflow 或 dry-run 时使用。可以在 P0/P1 仍可见的前提下继续 humanizer 和 format check，但必须把 unsupported 正文内容移到证据缺口区。

## 工作流程

1. **确定审计范围**
   - 判断用户需要逐段审计、source marker 审计、来源清单审计，还是可直接修订的问题列表。
   - 文件产出规则遵循 workflow §输出与文件安全。本阶段产物为 `.thesis-workflow/03-reference-audit.md`。
   - 如果存在 project ledger（`ledger/` 目录），读取 `ledger/facts.md` 和 `ledger/decisions.md` 后对照已确认事实、公式、来源和设计决策。

2. **切分草稿**
   - 按标题和段落切分。
   - 保留公式、图表占位符、表格和引用占位符。
   - 除非用户要求修改，否则不要重写整章。

3. **检查来源支撑**
   - 涉及逐段证据审计或 claim 分类时读取 `references/audit-rules.md`。
   - 每个包含事实或技术判断的段落，都应有 source marker、用户数据、设计假设、公式推导或清楚的内部推理。
   - 对照 `.thesis-workflow/materials-inventory.md`，用用户材料交叉校验：
     - 正文推导出的数值是否与用户材料一致 → 不一致标记 P1
     - 正文工程解释是否合理 → 不合理标记 P2
     - 标为设计假设的项是否确实无法推导/解释 → 可推导却标假设的标记为 P2
   - 标记无来源数量、性能比较、设备规格、标准、具名技术和研究现状判断。
   - 凡涉及行业标准、国家标准、规范、规程、验收要求、限值或标准条文，必须有可追溯来源。正文应说明标准名称、标准号、版本/年份、发布机构和适用条款或范围；缺关键要素时按 P1 或 P2 处理。
   - 标记”研究表明””相关文献指出”等没有连接来源的模糊归因。
   - 公式和计算要检查原始参数来源，以及派生参数是否有可复现计算链。
   - **文献不足时主动补搜（强制三级检索）**：发现缺来源的 claim 后，不只在审计报告中标记”缺文献”，必须按三级检索协议（Zotero → 用户 → 网络，见 source-policy.md）依次尝试补全。每级都要尝试，只有三级都未获取的才列入证据缺口清单。检索结果写入审计报告的”建议补充检索结果”栏，供修复阶段直接使用。

4. **检查公式和计算完整性**
   - 涉及公式审计时读取 `references/formula-audit-rules.md`。
   - 使用 project ledger 时读取 `references/project-ledger-audit-rules.md`。
   - 审计期间保持公式原样，除非用户要求修正。
   - 检查公式来源、符号定义、单位、代入步骤、结果精度和选型裕量。
   - 无法从前文参数复现的计算结果，按 P1 或更高处理。

5a. **检查 source marker 完整性**
   - 验证 `[参考文献]`、`[文献题名]`、`[网络资料: ...]`、`[标准规范: ...]`、`[Mxx]` 使用一致。
   - 把正文中残留的 `[标准规范: ...]` 视为工作稿标记。若标准已核验，建议改成正式正文表述和引用；若未核验，移入 `证据缺口清单`。
   - 把正文中的 `[待补来源: ...]` 视为残留 evidence gap marker，建议移入 `未写入正文的待补资料`、`证据缺口清单` 或 project ledger。
   - 正文中残留的 `[用户材料: ...]` 或 `[Mxx]` → 标记为 P3（最终输出前必须清除，不应留在正文中）。
   - Zotero/local source marker 应使用来源题名作为括号内容，例如 `[基于神经网络的悬臂式掘进机自适应截割控制系统研究]` 或 `[A development in rock cutting technology]`。
   - 重复题名需要在 marker 内追加作者和年份，例如 `[A development in rock cutting technology Hood 2000]`。
   - 检查图表占位符是否位于正文相关插入点，而不只是尾部清单。
   - **文献信息准确性抽查**：对照 Zotero 文献库或 `.bib` 导出文件（默认路径 `.thesis-workflow/evidence/zotero-export/`），随机抽查 20%（不少于 5 条）的 `[文献题名]` marker，核对题名、作者、年份是否与原始记录一致。题名被缩写、改写或包含转录错误（如特殊字符丢失、大小写错误）→ 标记 P2，需从原始记录修正。若 `.bib` 文件不存在，抽查 Zotero MCP 可检索到的条目。若 Zotero MCP 和 `.bib` 均不可用，在审计报告中标注"文献信息准确性未经核验"并建议用户提供导出文件。

5b. **对照文献笔记缓存校验正文 claim（⭐）**
   - 检查 `.thesis-workflow/literature-notes.md` 是否存在。
   - 如存在，读取缓存中与当前审计段落相关的文献条目。
   - **仅读取状态为 `已获取` 的条目**；标记为 `无笔记` 或 `获取失败` 的条目直接跳过，不重试获取。
   - 对照缓存中的标注内容，验证正文 claim 一致性：
     - 正文声称的定量结论（如"A 比 B 精度高 15%"）在标注中无对应数据 → 标记 P1
     - 正文引用的结论方向与标注内容相反 → 标记 P0
     - 正文 claim 在标注中有直接支撑 → 在审计报告中标记为"已验证（缓存）"
   - 标记为 `无笔记` 的文献无法交叉校验 → 在审计报告中标注"文献笔记缺失，无法交叉校验"，**不自动升级为 P0/P1**。确需原文核实的内容放入审计报告的"建议补充检索结果"栏。
   - 如某条待校验 claim 对应的文献笔记不在缓存中且状态非 `无笔记`/`获取失败`，可尝试通过 Zotero MCP 补获取（延续写作阶段的用户授权）。补获取同样每篇最多 1 次，失败后标记 `获取失败` 并跳过。

5c. **对照计算记录核验正文数据**
   - 检查 `.thesis-workflow/calculation-records.md` 是否存在（计算章）。如存在，对照核验正文中的数值、公式和选型结论是否与 records 一致。
   - 正文提到但 records 中无对应记录的计算结论 → 标记 P1。
   - 正文数值与 records 底稿不一致 → 标记 P1。
   - records 中引用的标准，检查其核验状态。`核验失败` 的标准仍在正文中用作设计依据 → 标记 P0。

6. **分类问题**
   - `P0`：疑似伪造、实质错误或可能改变论文结论的问题。
   - `P1`：重要事实、参数、公式、性能判断或文献归因缺来源或来源不匹配。
   - `P2`：有 marker 但不够清楚，后续 bibliography 或格式转换难以解析。
   - `P3`：风格、格式或一致性问题，可等到格式收尾阶段处理。

7. **建议下一步**
   - P0/P1 未解决时，先补证据或降级表述。
   - 标准或规范来源缺失时，建议检索方向应包含标准名称、标准号候选、发布机构、年份/版本和条文范围。
   - 只有 P2/P3 时，可以进入 `engineering-paper-humanizer`，再进入 `academic-format-cleaner`。
   - Validation mode 下，清楚区分“可为 workflow 测试继续润色”和“不可用于最终提交”。

## 审计输出

发现问题优先，默认使用这个结构：

1. `主要问题`
2. `逐段证据审查表`
3. `公式与计算审查表`
4. `用户材料交叉校验结果`（对照 materials-inventory.md 的一致性检查，含推导值对比、解释合理性评价、设计假设必要性判断）
5. `计算记录核验结果`（对照 calculation-records.md 的正文数据一致性，含数值偏差和所用标准核验状态）
6. `source marker 与来源清单问题`
7. `建议补充检索结果`（审计过程中主动检索到的候选文献，含题名、来源类型、检索词、可支撑段落）
8. `需要补充的资料`
9. `可直接进入后处理的部分`
10. `建议的下一步确认问题`

交接给 `engineering-paper-humanizer` 时，额外给出两个短清单：

- `可润色段落`：证据状态足以进入风格润色的段落。
- `禁止润色成定论的段落`：含 P0/P1、缺数据或 unsupported claims 的段落；润色前应移出正文或补证据。

### 门控状态文件

审计结束后，在 `.thesis-workflow/status.json` 写入机器可读的门控状态，供下游技能在启动时检查：

```json
{
    "stage": "audited",
    "timestamp": "2026-05-11T22:00:00",
    "p0_count": 0,
    "p1_count": 0,
    "green_paragraphs": ["§2.1", "§3.2"],
    "blocked_paragraphs": ["§2.3"],
    "next_allowed": "humanizer",  // 或 "fix-evidence"（P0/P1>0） / "next-chapter"（本章已完成）
    "notes": "简短说明"
}
```

- `p0_count` / `p1_count` 任一 > 0 时，`next_allowed` 设为 `"fix-evidence"`（必须退回补证据，禁止进入 humanizer，禁止开始下一章）。
- 仅当 P0/P1 全部解决后，`next_allowed` 设为 `"humanizer"`，放行进入润色。后续 `"format-cleaner"` 和 `"next-chapter"` 分别由 humanizer 和 format-cleaner 阶段完成后更新。

### 文献笔记缓存清理

审计报告完成且 `status.json` 写入后，根据审计结果清理 `.thesis-workflow/literature-notes.md`：

- `next_allowed = "humanizer"` 或 `"next-chapter"`（审计通过）→ 清空缓存内容，保留文件头和下一章占位：
  ```markdown
  # 文献笔记缓存

  > 上一章已完成。等待下一章写作。
  ```
- `next_allowed = "fix-evidence"`（审计未通过）→ **保留**缓存内容，供修复阶段继续使用。修复完成并重新审计通过后再清空。
- 全部章节完成后 → 清空缓存内容，保留文件（不删除），方便后续修改或增补章节时复用。

不要编造缺失来源。需要来源时，在 evidence gap section 中说明证据类型和可检索关键词，不要伪造参考文献，也不要把缺来源定论留在正文中。

## 参考文件

| 文件 | 用途 |
| --- | --- |
| `references/audit-rules.md` | 通用 claim 证据要求和 P0-P3 分级边界 |
| `references/formula-audit-rules.md` | 公式、参数、单位和计算链审计规则 |
| `references/project-ledger-audit-rules.md` | 使用 project ledger 时的对照审计规则 |
