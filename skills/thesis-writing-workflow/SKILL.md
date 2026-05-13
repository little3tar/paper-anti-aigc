---
name: thesis-writing-workflow
description: >-
  用于协调整套中文工程类毕业论文工作流。用户要求完整写论文/跑一遍论文流程/从头写论文、
  按流程来/该用哪个 skill/接下来做什么、complete thesis writing process、
  staged agent workflow、从任务书到大纲和章节、source audit、humanized revision、
  final format cleanup、approval checkpoints、output format confirmation、
  project ledger 或 multi-skill orchestration 时使用。
  默认按序执行全部五个阶段，用户明确指定范围时才允许局部执行。
---

# Thesis Writing Workflow

## Red Flags（停止并检查）

| AI的想法 | 正确做法 |
|---|---|
| “用户说'完整跑一遍'，全自动” | 预授权模式也须记录检查点，P0/P1 仍为阻塞项 |
| “用户没说生成文件，不创建” | 进入论文工作流后默认主动更新 `.thesis-workflow/` |
| “备份太麻烦，直接改主文件” | 修改主文件前必须 `git_snapshot.py` 备份 |
| “从 humanizer 开始更快 / 做完大纲就停” | 未指定范围时必须跑完 1→5；模糊说法需确认是只做一步还是继续后续 |
| “预授权模式，细纲也跳过确认” | 预授权只跳过文件生成/格式询问，细纲内容确认不跳过 |
| “用户说'写第X章'，细纲不用确认” | 必须输出细纲并等待用户显式确认，才能进入正文写作 |
| “用户给了电机型号，直接写成'MC51 采用 XX 电机'” | 用户提供的型号/参数必须先确认 A/B/C 分类，B 类禁止用 A 类语气写成产品定论 |

本 skill 是完整 thesis workflow 的 router。它不替代各阶段 skills，而是决定下一步该调用哪个 skill、何时暂停确认、何时阻止下游润色或格式收尾。

## 执行约束

**默认必须按 1→2→3→4→5 顺序执行全部五个阶段。** 用户要求”写论文””帮我跑一遍””完整论文写作”等未明确指定范围的请求，一律按完整流程执行，不跳过任何步骤。

仅当用户消息中**明确写出**”只运行 X””只做 X””只做第 X 步””只跑 X 和 Y”等限定词时，才将执行范围限制到用户指定的阶段。模糊说法如”先做大纲””从审计开始””润色一下”不算明确指定范围——这些情况下仍需确认：是只做这一步，还是从这一步开始并完成后续所有步骤。

### 例外场景（仅用户明确指定范围时）

用户明确说”只运行 X”时：

- 先检查该步骤的最低输入前提（见下方阶段输入契约）。
- 缺少前提时只补问必要问题，不要强行从第 1 步重跑完整流程。
- 若跳过的上游步骤会影响可靠性，在输出中说明假设和风险。

## 阶段输入契约

局部执行时按下表判断是否可以直接进入目标阶段：

| 阶段 | 最低输入前提 | 可选输入 | 阻塞条件 | 默认输出 |
| --- | --- | --- | --- | --- |
| `thesis-outline-planner` | 任务书、设计说明、导师要求或明确论文题目 | 已有文献、Zotero 导出、学校模板 | 研究对象或任务边界完全不明 | `.thesis-workflow/01-outline.md`（大纲）+ `literature-pool.md`（文献池全表） |
| `evidence-grounded-chapter-writer` | 已确认的大纲、章节目标或用户指定写作范围 | ledger/（事实+决策）、文献池、用户材料、图表/参数 | 缺少章节目标，或关键用户自有数据不可替代 | `.thesis-workflow/02-chapter-draft.md`；细纲写入 `outlines/chX-detailed.md` |
| `reference-integrity-auditor` | 已有大纲、章节草稿或小节草稿 | 来源清单、ledger/、标准规范、用户材料、calculation-records.md | 没有可审计文本 | `.thesis-workflow/03-reference-audit.md` |
| `engineering-paper-humanizer` | 待润色文本，且证据状态可接受或已明确为 validation mode | 审计报告、术语表、学校风格要求 | P0/P1 > 0 或 status.json 不存在，且非 validation mode | `.thesis-workflow/04-humanized.md`（润色操作记录，非全文副本） |
| `academic-format-cleaner` | 待清理文本或文件 | 学校模板、引用样式、LaTeX/Markdown 约束 | 正文仍含未处理 P0/P1、缺来源定论或 status.json 不存在 | `.thesis-workflow/05-format-cleaned.md`（格式操作记录，非全文副本） |

## 强制串行规则

每个阶段启动前，必须检查上游产物：

1. 读取 `.thesis-workflow/ledger/chapter-status.md`（如存在），确认上游阶段状态为 `confirmed`。首次运行（`ledger/` 目录尚不存在）时跳过此检查。
2. 读取目标阶段依赖的上游产物（如 `01-outline.md`、`02-chapter-draft.md`、`03-reference-audit.md`）。
3. 读取 `.thesis-workflow/ledger/facts.md` 和 `ledger/decisions.md`（如存在），获取已确认设计参数和决策。
4. 若上游产物不存在或状态非 `confirmed`，且用户未明确声明跳过，**拒绝执行**并提示先运行上游阶段。
5. `engineering-paper-humanizer` 额外检查 `status.json`：若 `p0_count` 或 `p1_count` > 0，**强制拒绝**，提示先运行 `reference-integrity-auditor`。
6. `academic-format-cleaner` 额外检查 `status.json`：若 `next_allowed` 不为 `"humanizer"` 或 `"format-cleaner"`，**强制拒绝**。
7. 跨章阻塞规则：前一章的 `status.json` 中 `next_allowed` 为 `"fix-evidence"` 时，**禁止开始下一章写作**。必须先将 P0/P1 清零并完成 humanizer+format-cleaner，`next_allowed` 变为 `"next-chapter"` 后才能进入下一章。
8. 细纲确认阻塞规则：在 `ledger/chapter-status.md` 中，当前章细纲状态非 `confirmed` 时，**禁止进入正文写作**（即 `evidence-grounded-chapter-writer` 的步骤 3 和步骤 4）。细纲状态为 `draft` 时不得继续。

## 审计退回修复闭环

当 `reference-integrity-auditor` 发现 P0/P1 问题时，进入以下闭环，不得跳过直接进入 humanizer：

```
审计发现问题（P0/P1 > 0）
    │
    ▼
status.json 写 next_allowed = "fix-evidence"（禁止进入 humanizer 和下一章）
    │
    ▼
逐项处理审计报告中的问题：
    ├── 缺文献 → 重新检索（Zotero / Web / 用户提供）
    ├── 缺参数 → 向用户索要或检索标准规范
    ├── source marker 不一致 → 修正 marker
    ├── 公式不可复现 → 补全推导链或标为设计假设
    └── 疑似伪造 → 删除或替换为可验证来源
    │
    ▼
修改章节草稿（02-chapter-draft.md），记录修复内容
    │
    ▼
重新运行 reference-integrity-auditor
    │
    ├── P0/P1 仍 > 0 → 继续循环
    │
    └── P0/P1 = 0 → status.json 写 next_allowed = "humanizer" → 放行进入润色
    └── humanizer + format-cleaner 完成 → status.json 写 next_allowed = "next-chapter"
```

**循环规则**：
- 每一轮审计必须更新 `03-reference-audit.md`，记录本轮新发现和已修复项。
- `ledger/questions.md` 或 `03-reference-audit.md` 记录每条 P0/P1 的修复决策和来源。
- 同一问题最多循环 3 轮；3 轮后仍未解决，将对应段落移出正文放入 `证据缺口清单`，在论文中显式标注为"待补证据"后继续。
- 用户可在任意一轮确认"该项接受当前状态"，标记为 `accepted-by-user` 后放行。

## 用户材料收录协议

用户可能提供任务书、参考资料、自己计算的数据、导师批注等。这些是**内部工作材料**，用于理解任务和规划写作，**不作为论文正式引用来源**，最终不进入主文件。

### 收录流程

**Step 0 — 检测与询问**

检测到用户消息中附带文件或资料时，主动询问：

> "检测到你提供了以下材料：[文件清单]。这些是论文写作的重要参考。是否同意我统一整理到 `.thesis-workflow/evidence/` 下，便于后续各阶段使用？"

- 用户同意 → 执行 Step 0a 分类确认
- 用户不同意 → 原地引用，记录原始路径到 `materials-inventory.md`
- 这是**一次性询问**，同批材料只问一次

**Step 0a — A/B/C 分类确认（⭐ 用户提供设计参数时必须执行）**

当用户提供了电机型号、泵型号、阀型号、压力/流量/功率参数、传感器选型等具体设计数据时，在整理前先确认数据性质：

> "你提供的这些参数（如 XX 型号、YY 数值），我需要确认数据性质，这会直接影响正文表述方式：
> - **A 类（产品公开规格）**：MC51 产品手册或数据表已有的参数 → 正文用'MC51 配备/采用...'，配外部引用
> - **B 类（你的设计选择）**：你自己经分析权衡后做的选型决策 → 正文用'本文选取/确定...'，说明选取依据
> - **C 类（待推导验证）**：目前仅有初值，需后续计算确认 → 正文展示推导过程或标为设计假设
>
> 请逐项确认（或给我一个整体分类），我会据此确定各参数的写作语气。"

- 用户明确分类 → 记录到 `materials-inventory.md` 和 `ledger/facts.md`，后续写作严格遵循
- 用户不确定 → 默认按 B 类处理（"本文选取..."），保守表述，等待用户后续确认
- 用户未回复此项 → 标记为 `[分类待确认]`，写作前再次询问，不可默认写成 A 类产品定论

**Step 1 — 分类整理（用户同意后）**

```
.thesis-workflow/evidence/
├── task-book/           ← 任务书、设计说明、开题报告
├── reference-materials/ ← 用户提供的论文、手册、教材副本
├── user-data/           ← 用户自算数据、实验记录、仿真结果
├── user-figures/        ← 用户自制的图、照片、截图
├── user-code/           ← 用户提供的程序、脚本
├── advisor-notes/       ← 导师批注、会议记录
├── standards-specs/     ← 用户提供的标准规范文件
└── zotero-export/       ← Zotero 导出的 .bib 文件（文献信息校验基准）
```

同名冲突时附加时间戳区分；二进制文件直接移动，文本文件统一转 UTF-8。

**Step 2 — 编目**

创建或更新 `.thesis-workflow/materials-inventory.md`：

| ID | 文件名 | 类型 | 路径 | 提取的关键信息 | 数据性质 | 适用章节 | 消化方式 |
|---|---|---|---|---|---|---|---|
| M01 | task-book.pdf | 任务书 | evidence/task-book/ | 设计目标、约束、交付物 | — | 全文 | 规划输入 |
| M02 | motor-datasheet.pdf | 数据表 | evidence/reference-materials/ | 额定 15kW、转速 1500rpm | A | §2.3 | 配外部引用 |
| M03 | calc-draft.xlsx | 用户计算 | evidence/user-data/ | 齿轮模数初算 m=3.2 | C | §3.1 | 待推导验证 |
| M04 | 设计参数清单 | 设计选择 | evidence/user-data/ | 选取 YX3-280M-4 电机 90kW | B | §2.3/§3.2 | 说明选取依据 |

数据性质列取值：`A`（产品公开规格）、`B`（用户设计选择）、`C`（待推导验证）、`—`（不适用）。

**Step 3 — 提取并纳入规划**

- 从材料中提取设计要求、已知参数、约束条件、导师意见
- 写入 `ledger/facts.md`，内部标注来源 `[Mxx]` 和数据性质（A/B/C）
- 标记哪些参数可直接用于规划，哪些需要后续找外部来源或推导
- A 类参数标注外部引用目标；B 类参数标注选取依据和推导章节；C 类参数标注需要的计算步骤

**Step 4 — 写作时消化用户材料（核心规则）**

用户材料提供的信息**不直接作为引用写进正文**。正文需要这些数据时按以下层级处理：

| 优先级 | 方式 | 说明 |
|---|---|---|
| ① | 找到外部公开来源 | 正常引用外部来源，用户材料仅作交叉校验（适用于 A 类参数） |
| ② | 通过公式/原理推导 | 正文展示推导过程（公式→代入→结果），数据自证其源，用户材料值作为校验基准 |
| ③ | 工程合理解释 | 用语言说明选取依据（如"类比同型号设备""按 XX 设计手册推荐值"等），适用于 B 类设计选择 |
| ④ | 标为设计假设 | 以上均不可行时，标 `[设计假设: 基于 Mxx，值取 XXX]`，仅限用户已确认的数据 |

**A/B/C 写作语气对照**（与 `evidence-grounded-chapter-writer` 的 A/B/C 分类表述规则一致）：

| 类别 | 正文语气 | 示例 |
|---|---|---|
| A 类（产品公开规格） | "MC51 采用/配备..." | "MC51 标配 R040672 型截割头" + 外部引用 |
| B 类（用户设计选择） | "本文选取/确定/选用..." | "本文选取 A10VSO140DR 型变量泵，基于...分析确定" + 推导章节引用 |
| C 类（待推导验证） | 不可写成定论 | 展示推导过程，或标 `[设计假设: ...]` |

工作稿中可用 `[Mxx]` 标记内部参考，**最终输出前必须全部清除**。

## 执行模式

### Review-gated mode

真实论文写作默认使用此模式。在总大纲确认、章节细纲确认、证据缺口、P0/P1 审计问题和真实论文主文件修改决策处暂停。运行产物文件的创建和更新不等同于内容确认；可以先写入 `.thesis-workflow/`，但未经确认的大纲、细纲或证据处理方案不能作为下游定稿依据。

### Preauthorized continuous mode

当用户明确表示确认步骤已经预授权时使用，例如“所有确认直接通过”“从头到尾跑一遍”“不要中断”“完整运行一次工作流”。

在此模式中：

- 把假定决策记录在 handoff、project ledger 或 validation report 中。
- 可以连续经过输出格式选择、文件生成和 ledger 更新检查点；但必须记录这些检查点已由用户预授权。
- **总大纲和章节细纲的内容确认不跳过。** 预授权只免除文件路径/格式询问和产物写入确认，大纲和细纲仍需用户显式确认后才能作为下游依据。
- unsupported facts、parameters、formulas 和 conclusions 不进入正文，改放入审计报告、handoff 或 project ledger。
- 对真实提交，P0/P1 仍是阻塞项；对 workflow validation，可以在问题可见且已移出正文后继续 humanizer 和 format checks。

### Validation mode

当用户要求测试、验证、dry-run 或检查 skill 行为时使用。保持证据集较小，明确标注 synthetic inputs，并把产物写到用户指定的 validation folder。

推荐 validation artifacts 放在 `.thesis-workflow/validation/`：

1. `task-book.md`
2. `project-ledger.md`
3. `01-outline.md`
4. `02-chapter-draft.md`
5. `03-reference-audit.md`
6. `04-humanized.md`
7. `05-final-format-cleaned.md`
8. `06-skill-workflow-review.md`

## 两阶段 Review Gate

每个阶段产出后，执行显式的两阶段审查：

### Stage 1：规范合规检查

| 检查项 | 适用阶段 |
|---|---|
| 字数是否达标 | 章节写作后 |
| 章节结构是否完整 | 大纲规划后、章节写作后 |
| Source marker 格式是否一致 | 章节写作后、审计后 |
| 引用格式是否符合模板要求 | 审计后、格式清理后 |
| 图表占位符是否在正文插入点 | 章节写作后 |

### Stage 2：质量检查

| 检查项 | 适用阶段 |
|---|---|
| 去 AI 化：无机械过渡词、无空壳强调句 | 润色后 |
| 证据边界：P0/P1 是否清零 | 审计后 |
| 正文污染：无过程性说明、无模板残留 | 各阶段 |
| 段落结构：优先连贯段落，不列表堆砌 | 章节写作后 |
| 公式完整性：来源、符号、代入、单位、裕量 | 章节写作后、审计后 |

### 自动化检查项

可直接通过脚本验证的检查项：

| 检查项 | 脚本/方式 | 通过条件 |
|---|---|---|
| 格式 error | `check_format.py <file>` | error 清零 |
| AI 痕迹 warning | `check_text.py <file>` | warning 可解释（非误报） |
| 三段式密度 | `check_text.py <file>` 聚合输出 | ≤ 2 处/千字 |
| 连接词泛滥率 | `check_text.py <file>` 聚合输出 | 段落首行连接词占比 ≤ 30% |
| P0/P1 清零 | 读取 `status.json` | `p0_count` = 0, `p1_count` = 0 |

### 不合格处理

- Stage 1 不通过 → 退回当前阶段修复，阻断消息示例："格式检查未通过：X 个 error、Y 个 warning。请修复后重新运行 `check_format.py`。"
- Stage 2 不通过 → 根据问题类型退回对应上游阶段，阻断消息示例："去 AI 化未达标：全文三段式密度为 X 处/千字（阈值 2）。请返回 humanizer 进一步改写。"
- 两次 Review 均通过 → 在 `ledger/chapter-status.md` 记录放行，进入全流程完成仪式。

## 多章节并行编排（可选）

当论文规模较大且平台支持子 Agent 时，使用 task packet 机制。

### Task Packet 格式

每章写作前创建 task packet：
- Scope：本章范围
- Files to read：需读取的上游产物
- Files allowed to edit：独占的文件
- Required evidence：证据来源列表
- Rejection checks：禁止事项
- Required artifacts：须产出的文件

### 约束

- 不同章节由不同 Agent 并行处理，每章文件独占。
- 并行完成后由主控 Agent 做一致性检查。
- 子 Agent 不可用时降级为顺序执行，不静默回退为一次性生成。

## 阶段顺序

1. **`thesis-outline-planner`**
   - **前置条件**：任务书、设计说明、导师要求或明确论文题目（一者即可）。
   - 解析任务书和要求。
   - 建立 Zotero-first 文献池。
   - 规划总大纲、图表占位符和任务要求映射。
   - 按用户主题判断每章的证据和计算需求，不强加固定领域章型。
   - Review-gated mode 下在总大纲处暂停确认。

2. **`evidence-grounded-chapter-writer`**
   - **前置条件**：`.thesis-workflow/01-outline.md` 存在且大纲已确认，或用户明确指定了写作范围。
   - 为选定章节生成细纲。
   - 只有章节包含建模、计算、设计选型、实验、仿真、算法或定量比较时，才添加公式/参数计划。
   - **细纲必须经用户显式确认后才能进入正文写作。** Review-gated 和 preauthorized 模式均适用——预授权不跳过细纲内容确认。
   - 检索证据并写出带 `[参考文献]`、title-based source marker 和图表占位符的章节草稿。

3. **`reference-integrity-auditor`**
   - **前置条件**：`.thesis-workflow/02-chapter-draft.md` 存在且章节草稿已完成，或用户提供了待审计文本。
   - 审计 unsupported claims、source marker consistency 和来源可靠性。
   - 审计公式、单位、参数来源、代入步骤和计算可复现性。
   - 对照 `.thesis-workflow/literature-notes.md` 缓存中的文献笔记/标注交叉校验正文 claim（缓存存在且条目状态为 `已获取` 时）。
   - Review-gated mode 下，如 P0/P1 仍存在则暂停。Validation mode 下，只有把 unsupported 正文内容移入 evidence-gap lists 或 ledger 后，才允许继续。
   - **阻断规则**：P0/P1 > 0 时 `status.json` 写 `"next_allowed": "fix-evidence"`，下游 humanizer 和 format-cleaner 必须拒绝，且**禁止开始下一章**。
   - **缓存清理**：审计通过后清空 `literature-notes.md`（保留文件头占位）；审计未通过则保留供修复阶段使用。

4. **`engineering-paper-humanizer`**
   - **前置条件**：`.thesis-workflow/status.json` 存在且 `p0_count` 和 `p1_count` 均为 0，或当前为 validation mode。
   - **硬性阻断**：若 `status.json` 不存在，说明审计未运行，拒绝继续。若 `p0_count` 或 `p1_count` > 0，拒绝继续，提示先运行 `reference-integrity-auditor` 补齐证据。
   - 只在证据问题受控后进行。
   - 降低 AI-like phrasing，但不改变技术含义、不发明数据、不补写来源。

5. **`academic-format-cleaner`**
   - **前置条件**：`.thesis-workflow/status.json` 存在且 `p0_count` 和 `p1_count` 均为 0，或已通过 humanizer 阶段。
   - **硬性阻断**：若 `status.json` 不存在，说明审计未运行，拒绝继续。若为 submission mode 且 P0/P1 > 0，拒绝继续。
   - 最后运行。
   - 修复 citation placement、Markdown/LaTeX/plain-text format、命令保护和残留占位符。

## 全流程完成仪式

当第 5 步 `academic-format-cleaner` 完成且两阶段 Review Gate 均通过后，执行以下收尾动作：

1. **汇总产物**：读取 `.thesis-workflow/` 中 01-05 全部产物，确认每个阶段产物均已更新且标记为通过。
2. **最终聚合检查**：
   - 运行 `check_text.py` 全文检测，确认三段式密度、连接词泛滥率等聚合指标未超阈值。
   - 运行 `check_format.py` 确认 error 清零。
   - 确认 `status.json` 中 `p0_count` 和 `p1_count` 均为 0。
3. **主动询问用户**：
   - "全部五个阶段已完成，审核均通过。是否将最终文本写入主文件？"
   - 如果论文有多个主文件（如各章独立），逐章确认写入目标。
4. **写入主文件**（用户确认后）：
   - 先通过 `git_snapshot.py <主文件>` 创建备份。
   - 将合并后的最终文本写入主文件。
   - 更新 `.thesis-workflow/ledger/chapter-status.md` 和 `operations-log.md`，记录写入时间、备份路径和最终版本号。
5. **交付清单**：在输出中列出主文件路径、备份路径、各阶段产物路径和推荐下一步（如：编译 LaTeX、提交导师审阅）。

## 主文件输出后的修改回环

全流程完成、文本写入 `main.md` / `main.txt` 后，用户审阅时可能发现需要修改。此时 `status.json` 中 `next_allowed` 为 `"next-chapter"`，PreToolUse 钩子已放行主文件写入。修改后的内容仍须经过润色和格式审核，不得因为"工作流已完成"就直接交付未处理的文本。

### 修改分级与处理路径

收到修改请求后，先判断修改幅度，按对应路径处理：

| 级别 | 判断标准 | 处理路径 |
|---|---|---|
| **L1 微调** | 错别字、标点修正、单个术语替换、数字勘误 | 直接改 `main.md`，无需重跑阶段。改后运行 `check_text.py` 和 `check_format.py` 确认无新增问题。 |
| **L2 局部重写** | 1-3 个句子重写、段落内结构调整、表述优化 | ① 先改 `main.md` ② 运行 `check_text.py` 复查 AI 腔指标 ③ 运行 `check_format.py` 复查格式 ④ 若检查未通过 → 对变更段落重跑 humanizer → 再跑 format-cleaner → 更新 `main.md` |
| **L3 内容变更** | 新增段落、删除段落、数据/结论改动、结构调整 | ① 先改 `02-chapter-draft.md`（内容权威源必须同步） ② 如变更涉及证据/数据，更新 `calculation-records.md` 和 `ledger/facts.md` ③ 对变更部分重跑 humanizer（阶段 4） ④ 重跑 format-cleaner（阶段 5） ⑤ 将处理后的文本更新到 `main.md` ⑥ 更新 `ledger/chapter-status.md` 和 `operations-log.md` |

### 修改回环的产物更新

| 修改级别 | 更新 `02-chapter-draft.md` | 更新 `04-humanized.md` | 更新 `05-format-cleaned.md` | 重跑检查脚本 |
|---|---|---|---|---|
| L1 | 不需要 | 不需要 | 不需要 | 建议（确认无新增问题） |
| L2 | 不需要 | 追加本轮变更记录 | 追加本轮变更记录 | 必须 |
| L3 | 必须 | 追加本轮变更记录 | 追加本轮变更记录 | 必须 |

### 回环中的备份

- L2 / L3 修改前，先通过 `git_snapshot.py <主文件>` 创建备份。
- L3 修改前额外备份 `02-chapter-draft.md`：`git_snapshot.py .thesis-workflow/02-chapter-draft.md`。
- 多次回环时，每次修改前均备份，不覆盖之前的备份。

### 禁止事项

- 不得因为"工作流已完成"就将 L2/L3 级修改直接写入 `main.md` 而不重跑检查和润色。
- L3 级修改不得只改 `main.md` 而不同步 `02-chapter-draft.md`——草稿是内容权威源，主文件是输出快照。
- 回环中不得修改 `status.json` 的 `next_allowed`——该字段只由审计阶段的正式流程更新。

## 输出与文件安全

- 区分“内容确认”和“文件更新”。真实论文工作流中，`.thesis-workflow/` 内运行产物应随每次相关阶段运行主动创建或更新；但总大纲、章节细纲、P0/P1 处理方案和真实论文主文件修改仍需要用户确认。
- 单独运行任一 thesis skill 时也遵循同一规则：若当前目录、用户指定目录或已识别的论文项目根目录中存在 `.thesis-workflow/`，或用户明确处于论文 workflow 项目中，则该 skill 运行结束必须更新对应阶段产物和必要的 `ledger/` 文件；不要因为用户没有再次说”生成文件”而跳过更新。
- 用户只要求一次性在对话中返回内容，且没有进入论文项目工作流时，可以不创建文件；一旦创建或使用 `.thesis-workflow/`，后续阶段默认读取并更新其中的相关产物。
- 阶段开始前先读取已有上游产物。若 `.thesis-workflow/ledger/` 存在，读取其中的 facts/decisions/chapter-status；若 `main-tex-context.md` 存在，读取项目结构地图。若目标阶段依赖大纲、草稿或审计报告，也读取对应的 `01-outline.md`、`02-chapter-draft.md` 或 `03-reference-audit.md`。
- 阶段结束后更新本阶段产物和 `ledger/` 对应文件（facts/decisions/chapter-status）。大纲阶段更新 `01-outline.md` 和 `literature-pool.md`，章节写作阶段更新 `02-chapter-draft.md`，证据审计阶段更新 `03-reference-audit.md`，润色阶段更新 `04-humanized.md`（操作记录），格式清理阶段更新 `05-format-cleaned.md`（操作记录）。
- `ledger/facts.md` 和 `ledger/decisions.md` 在确认新事实、参数、公式、来源、设计假设、用户材料或决策时更新。`ledger/chapter-status.md` 在每个阶段完成时更新。`main-tex-context.md` 只在论文主文件结构、章节标题、引用方案、模板或主文件路径变化时更新。
- 用户要求生成文件但未指定目录时，默认创建或使用论文项目根目录下的 `.thesis-workflow/`。如果当前工作目录位于 skill 仓库内，不能把运行产物写进 skill 仓库；应使用用户论文项目根目录，无法判断时先确认。
- 用户要求生成文件但未指定拆分方式时，将主要内容统一写入 `.thesis-workflow/` 内的默认主文件。中间表格、证据清单和待补材料作为主文件内的独立章节，除非用户指定拆成多个文件。
- 论文真实主文件优先使用用户提供或项目中可明确识别的现有主文件名；无法判断时先确认。若用户始终没有指定，才按目标格式使用 `main.tex`、`main.md` 或 `main.txt`。
- 推荐运行产物默认文件名按任务选择：`.thesis-workflow/01-outline.md`、`.thesis-workflow/02-chapter-draft.md`、`.thesis-workflow/03-reference-audit.md`、`.thesis-workflow/04-humanized.md`、`.thesis-workflow/05-format-cleaned.md`，不要把这些运行产物写进 skill 仓库。
- Project ledger 已拆分为 `ledger/` 子目录：`ledger/facts.md`（设计参数）、`ledger/decisions.md`（决策记录）、`ledger/chapter-status.md`（章节进展）、`ledger/questions.md`（待确认问题）。汇总索引文件为 `.thesis-workflow/project-ledger.md`。
- 文献池独立文件：`.thesis-workflow/literature-pool.md`（60条文献全表，6组分类，含 ZoteroKey 映射）。
- 章节细纲独立存放：`.thesis-workflow/outlines/chX-detailed.md`（每章一份，段落级写作点）。大纲文件 `01-outline.md` 只保留到小节标题层级。
- 批量操作日志：`.thesis-workflow/operations-log.md`（项目检查、章节清除等一次性操作记录，只追加不修改）。
- Project ledger 默认放在 `.thesis-workflow/project-ledger.md`；按 `main-tex-context-template.md` 生成的项目上下文默认放在 `.thesis-workflow/main-tex-context.md`。
- 文献笔记缓存默认放在 `.thesis-workflow/literature-notes.md`（临时文件，审计通过后清空）。
- 图表数据溯源清单默认放在 `.thesis-workflow/figure-data-manifest.md`（持久文件，数据文件路径、生成脚本、输出格式）。
- 计算记录默认放在 `.thesis-workflow/calculation-records.md`（计算底稿，正文数值的唯一权威数据源）。
- 每次直接修改用户论文主文件前，先通过 `engineering-paper-humanizer/scripts/git_snapshot.py <文件>` 创建备份。脚本优先使用 Git 分支备份，回退到 `.thesis-workflow/backups/` 下的文件复制备份。不要把备份写进 skill 仓库。
- 直接修改真实论文主文件（`main.md` / `main.txt`）后，将本轮变更清单（改了什么、为什么改）写入 `.thesis-workflow/` 对应阶段产物（`04-humanized.md` 或 `05-format-cleaned.md`）。这些产物是操作记录，不存全文副本——全文以 `main.md` / `main.txt` 为唯一权威输出。
- `.thesis-workflow/` 内运行产物默认主动更新，但不对每次更新创建备份；重要确认版、主文件结构大改、用户原始材料变更和真实主文件修改才创建备份或快照。重大确认版本建议使用 `--anchor` 参数创建锚点备份，锚点备份永不自动淘汰。
- 以下 `.thesis-workflow/` 产物在关键节点应额外备份：`ledger/` 目录（每次确认后）、`01-outline.md`（总大纲确认后）、`02-chapter-draft.md`（细纲确认后）。备份命令同主文件：`git_snapshot.py .thesis-workflow/01-outline.md --anchor`。
- 普通备份默认保留最近 5 个，超出自动淘汰（可通过 `GIT_SNAPSHOT_MAX_BACKUPS` 环境变量或 `--max-backups N` 参数调整）。锚点备份不受此限制。
- 多轮项目中，把输出格式、主文件路径、备份位置和已确认的文件生成授权记录到 project ledger 或 handoff。

### Skills 仓库维护文件

`tests/` 和 `evals/` 只用于维护 skills 仓库，不参与论文项目运行。修改脚本、规则 JSON、备份逻辑或输出路径策略时更新 `tests/`；修改 `SKILL.md` description、触发边界或工作流职责划分时更新 `evals/`。不要把这两个目录复制到论文项目的 `.thesis-workflow/` 中，也不要把论文项目运行产物写进它们。

### 备份协议

备份由 `engineering-paper-humanizer/scripts/git_snapshot.py` 统一执行。

直接改论文主文件前按此顺序处理：

1. 确认目标是用户论文主文件，不是 skill 仓库内的 `SKILL.md` 或脚本。
2. 调用 `git_snapshot.py <文件>` 创建备份。脚本自动选择 Git 分支备份（仓库内）或文件复制备份（非 Git 目录）。
3. 备份文件名格式：文件模式为 `<原文件名>_YYYYMMDD-HHMMSS-fff.<扩展名>`（毫秒精度）；Git 模式为 `backup/humanizer/YYYYMMDD-HHMMSS-fff` 分支。锚点备份在时间戳后附加 `-anchor` 标记。
4. 修改完成后，将本轮结果另存到对应阶段产物，例如 `04-humanized.md` 或 `05-format-cleaned.md`；若是章节写作或证据补全，则更新 `02-chapter-draft.md` 或 `03-reference-audit.md`。
5. 在输出或 handoff 中报告主文件路径、备份路径、另存产物路径和复查命令结果。
6. 普通备份自动保留最近 5 个（可配置），超出时静默淘汰最旧的。锚点备份永不自动淘汰。手动清理所有备份（含锚点）使用 `git_snapshot.py --cleanup`。

重要确认版本（大纲确认、细纲确认、主文件结构大改、用户原始材料变更）建议使用 `--anchor` 创建锚点备份，确保不会被自动淘汰覆盖。

## 用户材料与标准规范

用户材料的收录、整理和消化遵循上方"## 用户材料收录协议"。核心要点：用户材料是内部工作依据，不作为正式引用来源；正文中不得出现 `[用户材料: ...]` 或 `[Mxx]` 标记。

关于标准规范：

- 行业标准、国家标准、规范、规程、验收要求和限值不一定存在于用户 Zotero 文献库。需要此类依据时，先查本地文献和用户材料；不足时主动搜索官方标准平台、主管部门、标准发布机构、出版社页面或其他可靠来源。
- 已核验的标准规范应作为正式论文依据进入正文，用于支撑设计参数、限值、选型依据、验收要求或安全裕量。正文应说明标准名称、标准号、版本/年份和适用范围，并保留 `[参考文献]` 或学校模板要求的正式引用。
- 无法确认标准条文、版本、年份或适用范围时，不把对应要求写成定论；放入 `证据缺口清单` 并说明需要核验的标准名称、标准号、版本和条文范围。

## 确认问题

确认门只问当前必要问题，不要一次性问完所有问题。

可使用这些模板：

- 初始输出格式：”请确认输出格式：直接在对话中给出 Markdown，还是生成 `.tex`、`.md` 或 `.txt` 文件？未指定时我默认用对话 Markdown。”
- 论文主文件：”请确认论文主文件路径。若项目中已有明确的 `main.tex`、`thesis.tex`、`main.md` 或 `main.txt` 主文件，我将使用该文件；仍无法判断时再由你指定。”
- 总大纲确认：”请确认是否按此总大纲进入第 X 章细纲；如需调整，请指出章节或研究重点。”
- 细纲确认：”请确认本章细纲是否可以进入正文写作；如需调整，请指出需要增删的段落或图表。”
- 证据缺口：”以下内容缺少来源。请提供材料，或允许我改为网络检索/降级表述。”
- 真实主文件修改：”请确认是否直接修改论文主文件。确认后我会先备份原文件，再写回主文件，并把本轮结果另存到 `.thesis-workflow/` 对应阶段产物。”
- 材料收录：”检测到你提供了以下材料：[文件清单]。是否同意我统一整理到 `.thesis-workflow/evidence/` 下，便于后续各阶段使用？”
- 全流程完成：”全部五个阶段已完成，审核均通过。是否将最终文本写入主文件？”

## 输出默认值

- 独立一次性问答默认输出为对话 Markdown。
- 真实论文工作流默认主动创建或更新 `.thesis-workflow/` 运行产物；大纲、细纲和 P0/P1 处理方案仍需内容确认后才能进入下游。
- 草稿和中间审阅产物优先用 `.md`，且默认合并到 `.thesis-workflow/` 内的一个主文件中。
- `.docx` 不在直接输出格式之列。当用户要求 Word 文档时，先以 `.tex`、`.md` 或 `.txt` 完成内容并确认，再通过 pandoc 或 `python-docx` 转换为 `.docx`。
- 当用户要求 LaTeX 输出或提供了学校模板时，读取 `references/latex-output-guide.md` 生成 `.tex` 章节文件和 `main.tex`，然后通过 XeLaTeX 编译。

## Project Ledger

多轮 thesis 项目中，维护拆分后的 project ledger（`ledger/` 子目录），记录已确认事实、来源、公式、参数、设计决策和待补证据。索引文件为 `.thesis-workflow/project-ledger.md`。具体规则遵循 `references/project-ledger-rules.md`。

不要把项目特定事实、公式或数据写进 skill 文件夹。Skills 只保存可复用工作流规则。

## 数据单一权威源

- 所有计算类数值（缸径、推力、流量、功率等）的唯一权威源为 `.thesis-workflow/calculation-records.md`。正文和 ledger 中只引用计算记录 ID（如 C3-01），不复制数值。
- `ledger/facts.md` 只记录参数名、类型、来源和关联计算记录 ID。`main-tex-context.md` 引用 `ledger/facts.md`，不复制参数表。
- 数值变更/公式修正/代入纠错/标准选型调整时，只需更新 `calculation-records.md` 一处（旧记录标 `superseded`，追加新行，不原地编辑）。正文和 ledger 中引用计算记录 ID，数值自动跟随最新有效记录，无需多处同步。审计时对照计算记录核验正文数值。

## 阶段产物职责分离

- `02-chapter-draft.md`：章节正文草稿（**内容权威源**）。初稿不直接写入主文件。
- `03-reference-audit.md`：审计报告 + 文献修正记录（不存正文副本）。
- `04-humanized.md`：润色操作记录 + 变更清单（**不存全文副本**）。最终润色后文本写入 `main.md` / `main.txt`。
- `05-format-cleaned.md`：格式修复记录 + 变更清单（**不存全文副本**）。最终清理后文本写入 `main.md` / `main.txt`。
- `main.md` / `main.txt`：唯一对外输出文件。`main.md` 为 Markdown 中间格式，`main.txt` 为纯文本最终交付格式。

## Source Policy

遵循 `references/source-policy.md`。

核心规则：不能为了推动流程而发明看似有来源的 claim。unsupported facts、parameters、formulas 和 conclusions 不进入正文；应放入 `未写入正文的待补资料`、`证据缺口清单` 或 project ledger，或向用户索要材料。
