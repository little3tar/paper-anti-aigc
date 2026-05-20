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

> **本表是各阶段入口条件的权威参考。** 各子 skill 启动时的门控检查以本表的阻塞条件为准，§强制串行规则提供补充的自动化检查项（`status.json` 的 `next_allowed` 值校验）。

局部执行时按下表判断是否可以直接进入目标阶段：

| 阶段 | 最低输入前提 | 可选输入 | 阻塞条件 | 默认输出 |
| --- | --- | --- | --- | --- |
| `thesis-outline-planner` | 任务书、设计说明、导师要求或明确论文题目 | 已有文献、Zotero 导出、学校模板 | 研究对象或任务边界完全不明 | `.thesis-workflow/outline.md`（大纲）+ `literature-pool.md`（文献池全表） |
| `evidence-grounded-chapter-writer` | 已确认的大纲、章节目标或用户指定写作范围 | ledger/（事实+决策）、文献池、用户材料、图表/参数 | 缺少章节目标，或关键用户自有数据不可替代 | `.thesis-workflow/chapters/chX/draft.md`；细纲写入 `outlines/chX-detailed.md` |
| `reference-integrity-auditor` | 已有大纲、章节草稿或小节草稿 | 来源清单、ledger/、标准规范、用户材料、calculation-records.md | 没有可审计文本 | `.thesis-workflow/chapters/chX/audit.md` |
| `engineering-paper-humanizer` | 待润色文本（工作流模式：论文文件或章节；独立模式：用户粘贴的文本段落） | 审计报告、术语表、学校风格要求 | 工作流模式：P0/P1 > 0，或 status.json 不存在且非 validation mode，或 next_allowed 不为 humanizer/format-cleaner/next-chapter（详见 §强制串行规则第5条）。独立模式：无阻塞条件 | `.thesis-workflow/chapters/chX/humanized.md`（润色操作记录，非全文副本；独立模式不写产物） |
| `academic-format-cleaner` | 待清理文本或文件（工作流模式：论文文件；独立模式：用户粘贴的文本片段） | 学校模板、引用样式、LaTeX/Markdown 约束 | 工作流模式：P0/P1 > 0，或 status.json 不存在且非 validation mode，或 next_allowed 不为 format-cleaner/next-chapter（详见 §强制串行规则第6条）。独立模式：无阻塞条件 | `.thesis-workflow/chapters/chX/format-cleaned.md`（格式操作记录，非全文副本；独立模式不写产物） |

## 强制串行规则

> **本节是阶段门控逻辑的单一权威定义。** 各子 skill SKILL.md 和 PreToolUse 钩子中的门控条件均引用自此节。若其他位置的门控描述与此处不一致，以此处为准。

每个阶段启动前，必须检查上游产物：

1. 读取 `.thesis-workflow/ledger/chapter-status.md`（如存在），确认上游阶段状态为 `confirmed`。首次运行（`ledger/` 目录尚不存在）时跳过此检查。
2. 读取目标阶段依赖的上游产物（如 `outline.md`、`chapters/chX/draft.md`、`chapters/chX/audit.md`）。
3. 读取 `.thesis-workflow/ledger/facts.md` 和 `.thesis-workflow/ledger/decisions.md`（如存在），获取已确认设计参数和决策。
4. 若上游产物不存在或状态非 `confirmed`，且用户未明确声明跳过，**拒绝执行**并提示先运行上游阶段。
5. `engineering-paper-humanizer` 额外检查 `status.json`：若 `p0_count` 或 `p1_count` > 0，**强制拒绝**；若 `next_allowed` 不为 `"humanizer"`、`"format-cleaner"` 或 `"next-chapter"`，**强制拒绝**。`"format-cleaner"` 和 `"next-chapter"` 放行以支持修改回环。**独立润色模式**（用户在消息中直接粘贴文本，而非引用论文文件或章节）不适用本门控——humanizer 将跳过 `status.json` 检查，润色结果直接返回，不写入产物文件。
6. `academic-format-cleaner` 额外检查 `status.json`：若 `next_allowed` 不为 `"format-cleaner"` 或 `"next-chapter"`，**强制拒绝**。此条件与 PreToolUse 钩子防线2 一致——format-cleaner 必须在 humanizer 完成后运行。**独立模式**（用户在消息中直接粘贴文本，而非引用论文文件）不适用本门控。
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
    ├── 缺文献 → 重新检索（Zotero → 用户 → Web 三级检索，见来源策略）
    ├── 缺参数 → 向用户索要或检索标准规范
    ├── source marker 不一致 → 修正 marker
    ├── 公式不可复现 → 补全推导链或标为设计假设
    ├── 疑似伪造 → 删除或替换为可验证来源
    └── 每项修复后立即落盘：参数→ledger/facts.md，计算→calculation-records.md，决策→ledger/decisions.md
    │
    ▼
修改章节草稿（`chapters/chX/draft.md`），记录修复内容
    │
    ▼
重新运行 reference-integrity-auditor
    │
    ├── P0/P1 仍 > 0 → 继续循环
    │
    └── P0/P1 = 0 → status.json 写 next_allowed = "humanizer" → 放行进入润色
```

**循环规则**：
- 每一轮审计必须更新 `chapters/chX/audit.md`，记录本轮新发现和已修复项。
- `ledger/questions.md` 或 `chapters/chX/audit.md` 记录每条 P0/P1 的修复决策和来源。
- 同一问题最多循环 3 轮；3 轮后仍未解决，将对应段落移出正文放入 `证据缺口清单`，在论文中显式标注为"待补证据"后继续。
- 用户可在任意一轮确认"该项接受当前状态"，标记为 `accepted-by-user` 后放行。

## 用户材料收录协议

用户材料的收录、分类（A/B/C）、编目和消化规则见 `references/user-material-protocol.md`。核心要点：

- 用户材料是内部工作依据，**不作为正式引用来源进入正文**。
- 设计参数必须先确认 A/B/C 分类再写作，B 类禁止用 A 类语气写成产品定论。
- 正文中不得出现 `[用户材料: ...]` 或 `[Mxx]` 标记。

## 执行模式

### 工作流模式 vs 独立模式

本工作流中 humanizer 和 format-cleaner 两种 skill 支持两种入口：

| 模式 | 判断依据 | 门控行为 | 产物落盘 |
|------|---------|---------|---------|
| **工作流模式** | 用户引用论文文件或章节（如"润色 main-ch3.md"） | 完整检查 status.json（P0/P1 + next_allowed） | 写入 `chapters/chX/` |
| **独立模式** | 用户在消息中直接粘贴文本（如"润色以下文本：……"） | 跳过 status.json 检查 | 不写产物文件 |

子 skill 根据用户输入来源自动判断模式，无需用户手动指定。

### Review-gated mode（真实论文提交模式）

真实论文写作默认使用此模式（各子 skill 中亦称 submission mode）。在总大纲确认、章节细纲确认、证据缺口、P0/P1 审计问题和真实论文主文件修改决策处暂停。运行产物文件的创建和更新不等同于内容确认；可以先写入 `.thesis-workflow/`，但未经确认的大纲、细纲或证据处理方案不能作为下游定稿依据。

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
7. `05-format-cleaned.md`
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
   - **前置条件**：`.thesis-workflow/outline.md` 存在且大纲已确认，或用户明确指定了写作范围。
   - 为选定章节生成细纲。
   - 只有章节包含建模、计算、设计选型、实验、仿真、算法或定量比较时，才添加公式/参数计划。
   - **细纲必须经用户显式确认后才能进入正文写作。** Review-gated 和 preauthorized 模式均适用——预授权不跳过细纲内容确认。
   - 检索证据并写出带 `[参考文献]`、title-based source marker 和图表占位符的章节草稿。

3. **`reference-integrity-auditor`**
   - **前置条件**：`.thesis-workflow/chapters/chX/draft.md` 存在且章节草稿已完成，或用户提供了待审计文本。
   - 审计 unsupported claims、source marker consistency 和来源可靠性。
   - 审计公式、单位、参数来源、代入步骤和计算可复现性。
   - 对照 `.thesis-workflow/chapters/chX/literature-notes.md` 缓存中的文献笔记/标注交叉校验正文 claim（缓存存在且条目状态为 `已获取` 时）。
   - Review-gated mode 下，如 P0/P1 仍存在则暂停。Validation mode 下，只有把 unsupported 正文内容移入 evidence-gap lists 或 ledger 后，才允许继续。
   - **阻断规则**：P0/P1 > 0 时 `status.json` 写 `"next_allowed": "fix-evidence"`，下游 humanizer 和 format-cleaner 必须拒绝，且**禁止开始下一章**。

4. **`engineering-paper-humanizer`**
   - **前置条件**（工作流模式）：`.thesis-workflow/status.json` 存在且 `p0_count` 和 `p1_count` 均为 0，或当前为 validation mode。独立模式（用户粘贴文本）无前置条件。
   - **硬性阻断**（工作流模式）：若 `status.json` 不存在且非独立模式，说明审计未运行，提示用户先完成上游阶段。若 `p0_count` 或 `p1_count` > 0，拒绝继续，提示先运行 `reference-integrity-auditor` 补齐证据。
   - 只在证据问题受控后进行（工作流模式）。
   - 降低 AI-like phrasing，但不改变技术含义、不发明数据、不补写来源。

5. **`academic-format-cleaner`**
   - **前置条件**（工作流模式）：`.thesis-workflow/status.json` 存在且 `p0_count` 和 `p1_count` 均为 0，且 `next_allowed` 为 `"format-cleaner"` 或 `"next-chapter"`（即已完成 humanizer）。独立模式（用户粘贴文本）无前置条件。
   - **硬性阻断**（工作流模式）：若 `status.json` 不存在且非独立模式，提示用户先完成上游阶段。若 `p0_count` 或 `p1_count` > 0，拒绝继续。若 `next_allowed` 不为 `"format-cleaner"` 或 `"next-chapter"`，拒绝继续。完整的门控逻辑见 §强制串行规则第6条。
   - 最后运行。
   - 修复 citation placement、Markdown/LaTeX/plain-text format、命令保护和残留占位符。

## 全流程完成仪式

当第 5 步 `academic-format-cleaner` 完成且两阶段 Review Gate 均通过后，执行以下收尾动作：

1. **汇总产物**：读取 `.thesis-workflow/chapters/chX/` 中全部阶段产物，确认每个阶段产物均已更新且标记为通过。
2. **最终聚合检查**：
   - 运行 `check_text.py` 全文检测，确认三段式密度、连接词泛滥率等聚合指标未超阈值。
   - 运行 `check_format.py` 确认 error 清零。
   - 确认 `status.json` 中 `p0_count` 和 `p1_count` 均为 0。
3. **主动询问用户**：每章完成即写入对应章文件。全论文完成后逐章确认最终版本："第 X 章已完成，是否更新 `main-chX.md`？"，无需合并所有章到一个文件。
4. **写入主文件**（用户确认后）：
   - 先通过 `git_snapshot.py <主文件>` 创建备份。
   - **从 draft 抽取主文件正文**：`draft.md` 是工作稿（含10项产出元数据），写入主文件前剥离工作稿元数据，只保留以下内容进入主文件：
     - 正文（章节标题、段落、图表占位符、表注）
     - 参考文献引用（`[文献题名]` marker 保留在原句中）
     - Mermaid 代码块、matplotlib 脚本、Graphviz DOT 代码块（嵌入对应图表占位符下方，不在文末独立成章）
     - 提示词模板（嵌入对应图表占位符下方）
     - 表格正文（含表注）
   - 以下工作稿元数据**不进入主文件**：证据表、参考来源清单、待用户补充的信息、未写入正文的待补资料、证据缺口清单、后处理建议、章节细纲、公式与参数计划。
   - 将最终文本写入对应章文件 `main-chX.md` / `main-chX.txt` / `main-chX.tex`。
   - 更新 `.thesis-workflow/ledger/chapter-status.md` 和 `operations-log.md`，记录写入时间、备份路径和最终版本号。
5. **交付清单**：在输出中列出主文件路径（每章 1 个）、备份路径、各阶段产物路径和推荐下一步（如：编译 LaTeX、提交导师审阅）。

## 主文件输出后的修改回环

修改分级（L1/L2/L3）、产物更新和备份规则见 `references/revision-loop.md`。核心要点：

- L1 微调直接改主文件；L2 局部重写需复查检查脚本；L3 内容变更必须同步 `chapters/chX/draft.md`（内容权威源）。
- 任何级别修改均不得跳过润色和格式检查直接交付。
- 回环中不得修改 `status.json` 的 `next_allowed`。

## 输出与文件安全

- 区分“内容确认”和“文件更新”。真实论文工作流中，`.thesis-workflow/` 内运行产物应随每次相关阶段运行主动创建或更新；但总大纲、章节细纲、P0/P1 处理方案和真实论文主文件修改仍需要用户确认。
- 单独运行任一 thesis skill 时也遵循同一规则：若当前目录、用户指定目录或已识别的论文项目根目录中存在 `.thesis-workflow/`，或用户明确处于论文 workflow 项目中，则该 skill 运行结束必须更新对应阶段产物和必要的 `ledger/` 文件；不要因为用户没有再次说”生成文件”而跳过更新。
- 用户只要求一次性在对话中返回内容，且没有进入论文项目工作流时，可以不创建文件；一旦创建或使用 `.thesis-workflow/`，后续阶段默认读取并更新其中的相关产物。
- 阶段开始前先读取已有上游产物。若 `.thesis-workflow/ledger/` 存在，读取其中的 facts/decisions/chapter-status；若 `main-tex-context.md` 存在，读取项目结构地图。若目标阶段依赖大纲、草稿或审计报告，也读取对应的 `outline.md`、`chapters/chX/draft.md` 或 `chapters/chX/audit.md`。
- 阶段结束后更新本阶段产物和 `ledger/` 对应文件（facts/decisions/chapter-status）。大纲阶段更新 `outline.md` 和 `literature-pool.md`，章节写作阶段更新 `chapters/chX/draft.md`，证据审计阶段更新 `chapters/chX/audit.md`，润色阶段更新 `chapters/chX/humanized.md`（操作记录），格式清理阶段更新 `chapters/chX/format-cleaned.md`（操作记录）。
- `ledger/facts.md` 和 `ledger/decisions.md` 在确认新事实、参数、公式、来源、设计假设、用户材料或决策时更新。`ledger/chapter-status.md` 在每个阶段完成时更新。`main-tex-context.md` 只在论文主文件结构、章节标题、引用方案、模板或主文件路径变化时更新。
- 用户要求生成文件但未指定目录时，默认创建或使用论文项目根目录下的 `.thesis-workflow/`。如果当前工作目录位于 skill 仓库内，不能把运行产物写进 skill 仓库；应使用用户论文项目根目录，无法判断时先确认。
- 用户要求生成文件但未指定格式时，默认按章拆分输出 `main-chX.md` / `main-chX.txt` / `main-chX.tex`（每章一个独立文件）。如项目中已有明确的各章独立文件（如 `chapters/ch1.tex`），优先沿用现有命名。
- 论文真实主文件优先使用用户提供或项目中可明确识别的现有文件名；无法判断时先确认。若用户始终没有指定，按章使用 `main-chX.md` / `main-chX.txt` / `main-chX.tex`。
- 推荐运行产物默认文件名按任务选择：大纲为 `.thesis-workflow/outline.md`，章节写作产物按章归档为 `.thesis-workflow/chapters/chX/draft.md`、`.thesis-workflow/chapters/chX/audit.md`、`.thesis-workflow/chapters/chX/humanized.md`、`.thesis-workflow/chapters/chX/format-cleaned.md`，不要把这些运行产物写进 skill 仓库。
- Project ledger 已拆分为 `ledger/` 子目录：`ledger/facts.md`（设计参数）、`ledger/decisions.md`（决策记录）、`ledger/chapter-status.md`（章节进展）、`ledger/questions.md`（待确认问题）。汇总索引文件为 `.thesis-workflow/project-ledger.md`。
- 文献池独立文件：`.thesis-workflow/literature-pool.md`（文献全表，含 ZoteroKey 映射，分组管理）。
- 章节细纲独立存放：`.thesis-workflow/outlines/chX-detailed.md`（每章一份，段落级写作点）。大纲文件 `outline.md` 只保留到小节标题层级。
- 批量操作日志：`.thesis-workflow/operations-log.md`（项目检查、章节清除等一次性操作记录，只追加不修改）。
- Project ledger 默认放在 `.thesis-workflow/project-ledger.md`；按 `main-tex-context-template.md` 生成的项目上下文默认放在 `.thesis-workflow/main-tex-context.md`。
- 文献笔记缓存按章存储：`.thesis-workflow/chapters/chX/literature-notes.md`（随章保留，不自动清空）。
- 图表数据溯源清单默认放在 `.thesis-workflow/figure-data-manifest.md`（持久文件，数据文件路径、生成脚本、输出格式）。
- 计算记录默认放在 `.thesis-workflow/calculation-records.md`（计算底稿，正文数值的唯一权威数据源）。
- 每次直接修改用户论文主文件前，先通过 `scripts/git_snapshot.py <文件>` 创建备份。脚本优先使用 Git 分支备份，回退到 `.thesis-workflow/backups/` 下的文件复制备份。不要把备份写进 skill 仓库。备份对应章文件 `main-chX.md` / `main-chX.txt` / `main-chX.tex`。
- 直接修改真实论文主文件后，将本轮变更清单（改了什么、为什么改）写入 `.thesis-workflow/chapters/chX/` 对应阶段产物（`humanized.md` 或 `format-cleaned.md`）。这些产物是操作记录，不存全文副本——全文以主文件为唯一权威输出。
- `.thesis-workflow/` 内运行产物默认主动更新，但不对每次更新创建备份；重要确认版、主文件结构大改、用户原始材料变更和真实主文件修改才创建备份或快照。重大确认版本建议使用 `--anchor` 参数创建锚点备份，锚点备份永不自动淘汰。
- 以下 `.thesis-workflow/` 产物在关键节点应额外备份：`ledger/` 目录（每次确认后）、`outline.md`（总大纲确认后）、`chapters/chX/draft.md`（细纲确认后）。备份命令同主文件：`git_snapshot.py .thesis-workflow/outline.md --anchor`。
- 普通备份默认保留最近 5 个，超出自动淘汰（可通过 `GIT_SNAPSHOT_MAX_BACKUPS` 环境变量或 `--max-backups N` 参数调整）。锚点备份不受此限制。
- 多轮项目中，把输出格式、主文件路径、备份位置和已确认的文件生成授权记录到 project ledger 或 handoff。

### Skills 仓库维护文件

`tests/` 和 `evals/` 只用于维护 skills 仓库，不参与论文项目运行。修改脚本、规则 JSON、备份逻辑或输出路径策略时更新 `tests/`；修改 `SKILL.md` description、触发边界或工作流职责划分时更新 `evals/`。不要把这两个目录复制到论文项目的 `.thesis-workflow/` 中，也不要把论文项目运行产物写进它们。

### 备份协议

备份由 `scripts/git_snapshot.py` 统一执行。

直接改论文主文件前按此顺序处理：

1. 确认目标是用户论文主文件，不是 skill 仓库内的 `SKILL.md` 或脚本。
2. 调用 `git_snapshot.py <文件>` 创建备份。脚本自动选择 Git 分支备份（仓库内）或文件复制备份（非 Git 目录）。
3. 备份文件名格式：文件模式为 `<原文件名>_YYYYMMDD-HHMMSS-NN.<扩展名>`（NN 为厘秒精度，由脚本自动生成）；Git 模式为 `backup/humanizer/YYYYMMDD-HHMMSS-NN` 分支。锚点备份在时间戳后附加 `-anchor` 标记。手动创建的备份建议沿用同格式并附加说明性后缀（如 `-r2` 表示第二轮修订）。
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

- 初始输出格式：“请确认输出格式：直接在对话中给出 Markdown，还是生成 `.tex`、`.md` 或 `.txt` 文件？未指定时我默认用对话 Markdown。”
- 论文主文件：“请确认论文主文件命名。默认按章使用 `main-ch1.md` ~ `main-chN.md`。若项目中已有明确的章文件，我将沿用现有命名。”
- 总大纲确认：“请确认是否按此总大纲进入第 X 章细纲；如需调整，请指出章节或研究重点。”
- 细纲确认：”请确认本章细纲是否可以进入正文写作；如需调整，请指出需要增删的段落或图表。”
- 证据缺口：”以下内容缺少来源。请提供材料，或允许我改为网络检索/降级表述。”
- 真实主文件修改：”请确认是否直接修改论文主文件。确认后我会先备份原文件，再写回主文件，并把本轮结果另存到 `.thesis-workflow/` 对应阶段产物。”
- 材料收录：”检测到你提供了以下材料：[文件清单]。是否同意我统一整理到 `.thesis-workflow/evidence/` 下，便于后续各阶段使用？”
- 全流程完成：“第 X 章已通过全部五个阶段，审核均通过。是否将最终文本写入 `main-chX.md` / `main-chX.txt` / `main-chX.tex`？”

### 用户确认/补充信息的落盘规则（⭐ 全流程适用）

用户在**任何确认门**的回复中提供的新信息、纠正、补充细节，**必须在回复后立即写入对应 ledger 文件**，不得等到下一阶段或写作时再补。对话上下文可能被压缩，用户纠正的信息会丢失。

| 信息类型 | 落盘目标 | 操作 |
|---|---|---|
| 新确认/修正的参数（B 类设计选择、C 类初值更新等） | `ledger/facts.md` | 追加新行，旧值标 `superseded` |
| 计算类数值的修正（如”缸径改为 100mm”） | `calculation-records.md` | 旧记录标 `superseded`，追加新行，附修正说明 |
| 新确认的决策（选型方向、计算方法、输出格式等） | `ledger/decisions.md` | 追加新行 |
| 新增的待确认问题 | `ledger/questions.md` | 追加新行 |
| 补充的文献/来源/标准 | `literature-pool.md` | 追加新行 |
| 用户对 P0/P1 修复的确认或替代方案 | `03-reference-audit.md` | 追加修复记录 |
| 用户提供的补充材料/数据 | `materials-inventory.md` | 追加编目行 |

此规则覆盖**所有确认门**：总大纲确认、细纲确认、证据缺口确认、材料收录确认、A/B/C 分类确认、审计修复确认、主文件修改确认。

落盘后向用户一句话确认：”以上信息已写入 `ledger/facts.md` / `calculation-records.md`。”

## 输出默认值

- 独立一次性问答默认输出为对话 Markdown。
- 真实论文工作流默认主动创建或更新 `.thesis-workflow/` 运行产物；大纲、细纲和 P0/P1 处理方案仍需内容确认后才能进入下游。
- 草稿和中间审阅产物优先用 `.md`，写入 `.thesis-workflow/chapters/chX/` 下对应产物文件。
- **主文件输出格式**：按章节拆分，每章一个独立输出文件：
  ```
  main-ch1.md / main-ch1.txt  ← 第 1 章输出
  main-ch2.md / main-ch2.txt  ← 第 2 章输出
  ...
  main-chN.md / main-chN.txt  ← 第 N 章输出
  ```
- 每章独立跑完 2→3→4→5 阶段后即可写入对应章文件，无需等全论文完成。修改回环规则按章独立适用——改哪章就对该章文件执行备份和 L1/L2/L3 处理。
- 如果论文项目已有明确的各章独立文件（如 `chapters/ch1.tex`），优先沿用现有命名。主文件命名确认后记录到 `ledger/decisions.md`。
- `.docx` 不在直接输出格式之列。当用户要求 Word 文档时，先以 `.md` 或 `.txt` 完成内容并确认，再通过 pandoc 或 `python-docx` 转换为 `.docx`。
- 当用户要求 LaTeX 输出或提供了学校模板时，读取 `references/latex-output-guide.md` 生成 `.tex` 章节文件和 `main.tex`，然后通过 XeLaTeX 编译。

## Project Ledger

多轮 thesis 项目中，维护拆分后的 project ledger（`ledger/` 子目录），记录已确认事实、来源、公式、参数、设计决策和待补证据。索引文件为 `.thesis-workflow/project-ledger.md`。具体规则遵循 `references/project-ledger-rules.md`。

不要把项目特定事实、公式或数据写进 skill 文件夹。Skills 只保存可复用工作流规则。

## 数据单一权威源

- 所有计算类数值（缸径、推力、流量、功率等）的唯一权威源为 `.thesis-workflow/calculation-records.md`。正文和 ledger 中只引用计算记录 ID（如 C3-01），不复制数值。
- `ledger/facts.md` 只记录参数名、类型、来源和关联计算记录 ID。`main-tex-context.md` 引用 `ledger/facts.md`，不复制参数表。
- 数值变更/公式修正/代入纠错/标准选型调整时，只需更新 `calculation-records.md` 一处（旧记录标 `superseded`，追加新行，不原地编辑）。正文和 ledger 中引用计算记录 ID，数值自动跟随最新有效记录，无需多处同步。审计时对照计算记录核验正文数值。

## 阶段产物职责分离

- `chapters/chX/draft.md`：第 X 章正文草稿（**内容权威源**，**全量覆盖写入**，不追加）。每次写作完成后用最新完整草稿覆盖，文件中始终只有当前最新版本。初稿不直接写入主文件。按章隔离，不同章的草稿不互相覆盖。
- `chapters/chX/audit.md`：第 X 章审计报告 + 文献修正记录（**全量覆盖写入**，不追加）。每轮审计用最新完整报告覆盖，报告中包含本轮全部问题及修复状态。不存正文副本。按章隔离。
- `chapters/chX/humanized.md`：第 X 章润色操作记录 + 变更清单（**不存全文副本**）。至少记录高风险片段对照、marker 完整性确认结论和 check_text.py 复查关键指标。最终润色后文本写入主文件。
- `chapters/chX/format-cleaned.md`：第 X 章格式修复记录 + 变更清单（**不存全文副本**）。至少记录 marker 逐条核对结果、Unicode 转义序列检查结论和 check_format.py 最终 error 数。最终清理后文本写入主文件。
- 主文件（`main-chX.md` / `main-chX.txt` / `main-chX.tex`）：第 X 章唯一对外输出文件。`.md` 为 Markdown 中间格式，`.txt` 为纯文本最终交付格式。

## Source Policy

遵循 `references/source-policy.md`。

核心规则：不能为了推动流程而发明看似有来源的 claim。unsupported facts、parameters、formulas 和 conclusions 不进入正文；应放入 `未写入正文的待补资料`、`证据缺口清单` 或 project ledger，或向用户索要材料。
