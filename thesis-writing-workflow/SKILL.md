---
name: thesis-writing-workflow
description: >-
  用于协调整套或局部的中文工程类毕业论文工作流。用户要求 complete thesis writing process、
  staged agent workflow、从任务书到大纲和章节、source audit、humanized revision、final format cleanup、
  approval checkpoints、output format confirmation、project ledger 或 multi-skill orchestration 时使用。
  可路由完整流程，也可只执行其中一个或两个阶段。
---

# Thesis Writing Workflow

本 skill 是完整 thesis workflow 的 router。它不替代各阶段 skills，而是决定下一步该调用哪个 skill、何时暂停确认、何时阻止下游润色或格式收尾。

## 可局部执行

完整流程不是强制串行。用户可以直接请求其中一个步骤，或组合相邻的两个步骤完成一个任务，例如：

- 只做 `thesis-outline-planner`：根据任务书生成总大纲和资料需求。
- 只做 `evidence-grounded-chapter-writer`：在已有大纲、章节目标或用户给定材料足够时，直接写某一章或某一节。
- 只做 `reference-integrity-auditor`：审计用户已有草稿，不要求重新规划或重写。
- 只做 `engineering-paper-humanizer`：润色证据状态已经可接受的段落。
- 只做 `academic-format-cleaner`：修复已定稿文本的 LaTeX/Markdown/plain text 格式问题。
- 组合两步：例如“审计并润色”“润色并格式清理”“写第 3 章并做证据审计”。

局部执行时，先检查该步骤的最低输入前提。缺少前提时只补问必要问题，不要强行从第 1 步重跑完整流程。若跳过的上游步骤会影响可靠性，在输出中说明假设和风险。

## 阶段输入契约

局部执行时按下表判断是否可以直接进入目标阶段：

| 阶段 | 最低输入前提 | 可选输入 | 阻塞条件 | 默认输出 |
| --- | --- | --- | --- | --- |
| `thesis-outline-planner` | 任务书、设计说明、导师要求或明确论文题目 | 已有文献、Zotero 导出、学校模板 | 研究对象或任务边界完全不明 | `.thesis-workflow/01-outline.md` 或对话 Markdown |
| `evidence-grounded-chapter-writer` | 已确认的大纲、章节目标或用户指定写作范围 | project ledger、文献池、用户材料、图表/参数 | 缺少章节目标，或关键用户自有数据不可替代 | `.thesis-workflow/02-chapter-draft.md` 或对话 Markdown |
| `reference-integrity-auditor` | 已有大纲、章节草稿或小节草稿 | 来源清单、ledger、标准规范、用户材料 | 没有可审计文本 | `.thesis-workflow/03-reference-audit.md` 或对话 Markdown |
| `engineering-paper-humanizer` | 待润色文本，且证据状态可接受或已明确为 validation mode | 审计报告、术语表、学校风格要求 | P0/P1 未处理且用户不是在做 validation | `.thesis-workflow/04-humanized.md`、原主文件或对话 Markdown |
| `academic-format-cleaner` | 待清理文本或文件 | 学校模板、引用样式、LaTeX/Markdown 约束 | 正文仍含未处理 P0/P1 或缺来源定论 | `.thesis-workflow/05-format-cleaned.md`、原主文件或对话 Markdown |

## 执行模式

### Review-gated mode

真实论文写作默认使用此模式。在总大纲确认、章节细纲确认、证据缺口、P0/P1 审计问题和真实论文主文件修改决策处暂停。运行产物文件的创建和更新不等同于内容确认；可以先写入 `.thesis-workflow/`，但未经确认的大纲、细纲或证据处理方案不能作为下游定稿依据。

### Preauthorized continuous mode

当用户明确表示确认步骤已经预授权时使用，例如“所有确认直接通过”“从头到尾跑一遍”“不要中断”“完整运行一次工作流”。

在此模式中：

- 把假定决策记录在 handoff、project ledger 或 validation report 中。
- 可以连续经过输出格式、总大纲、细纲、ledger 创建和文件生成检查点；但必须记录这些检查点已由用户预授权。
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

## 阶段顺序

1. **`thesis-outline-planner`**
   - 解析任务书和要求。
   - 建立 Zotero-first 文献池。
   - 规划总大纲、图表占位符和任务要求映射。
   - 按用户主题判断每章的证据和计算需求，不强加固定领域章型。
   - Review-gated mode 下在总大纲处暂停确认。

2. **`evidence-grounded-chapter-writer`**
   - 为选定章节生成细纲。
   - 只有章节包含建模、计算、设计选型、实验、仿真、算法或定量比较时，才添加公式/参数计划。
   - Review-gated mode 下在细纲处暂停确认。
   - 检索证据并写出带 `[参考文献]`、title-based source marker 和图表占位符的章节草稿。

3. **`reference-integrity-auditor`**
   - 审计 unsupported claims、source marker consistency 和来源可靠性。
   - 审计公式、单位、参数来源、代入步骤和计算可复现性。
   - Review-gated mode 下，如 P0/P1 仍存在则暂停。Validation mode 下，只有把 unsupported 正文内容移入 evidence-gap lists 或 ledger 后，才允许继续。

4. **`engineering-paper-humanizer`**
   - 只在证据问题受控后进行。
   - 降低 AI-like phrasing，但不改变技术含义、不发明数据、不补写来源。

5. **`academic-format-cleaner`**
   - 最后运行。
   - 修复 citation placement、Markdown/LaTeX/plain-text format、命令保护和残留占位符。

## 输出与文件安全

- 区分“内容确认”和“文件更新”。真实论文工作流中，`.thesis-workflow/` 内运行产物应随每次相关阶段运行主动创建或更新；但总大纲、章节细纲、P0/P1 处理方案和真实论文主文件修改仍需要用户确认。
- 单独运行任一 thesis skill 时也遵循同一规则：若当前目录、用户指定目录或已识别的论文项目根目录中存在 `.thesis-workflow/`，或用户明确处于论文 workflow 项目中，则该 skill 运行结束必须更新对应阶段产物和必要的 `project-ledger.md`；不要因为用户没有再次说“生成文件”而跳过更新。
- 用户只要求一次性在对话中返回内容，且没有进入论文项目工作流时，可以不创建文件；一旦创建或使用 `.thesis-workflow/`，后续阶段默认读取并更新其中的相关产物。
- 阶段开始前先读取已有上游产物，至少包括 `.thesis-workflow/project-ledger.md` 和 `.thesis-workflow/main-tex-context.md`；若目标阶段依赖大纲、草稿或审计报告，也读取对应的 `01-outline.md`、`02-chapter-draft.md` 或 `03-reference-audit.md`。
- 阶段结束后更新本阶段产物和 `project-ledger.md`。大纲阶段更新 `01-outline.md`，章节写作阶段更新 `02-chapter-draft.md`，证据审计阶段更新 `03-reference-audit.md`，润色阶段更新 `04-humanized.md`，格式清理阶段更新 `05-format-cleaned.md`。
- `project-ledger.md` 在确认新事实、参数、公式、来源、设计假设、用户材料或决策时更新。`main-tex-context.md` 只在论文主文件结构、章节标题、引用方案、模板、关键参数表或主文件路径变化时更新。
- 用户要求生成文件但未指定目录时，默认创建或使用论文项目根目录下的 `.thesis-workflow/`。如果当前工作目录位于 skill 仓库内，不能把运行产物写进 skill 仓库；应使用用户论文项目根目录，无法判断时先确认。
- 用户要求生成文件但未指定拆分方式时，将主要内容统一写入 `.thesis-workflow/` 内的默认主文件。中间表格、证据清单和待补材料作为主文件内的独立章节，除非用户指定拆成多个文件。
- 论文真实主文件优先使用用户提供或项目中可明确识别的现有主文件名；无法判断时先确认。若用户始终没有指定，才按目标格式使用 `main.tex`、`main.docx` 或 `main.md`。
- 推荐运行产物默认文件名按任务选择：`.thesis-workflow/01-outline.md`、`.thesis-workflow/02-chapter-draft.md`、`.thesis-workflow/03-reference-audit.md`、`.thesis-workflow/04-humanized.md`、`.thesis-workflow/05-format-cleaned.md`，不要把这些运行产物写进 skill 仓库。
- Project ledger 默认放在 `.thesis-workflow/project-ledger.md`；按 `main-tex-context-template.md` 生成的项目上下文默认放在 `.thesis-workflow/main-tex-context.md`。
- 每次直接修改用户论文主文件前，先创建备份。复制备份默认写入 `.thesis-workflow/backups/`，不要把备份写进 skill 仓库。
- 直接修改真实论文主文件后，即使已经写回主文件，也要把本轮修改结果另存到 `.thesis-workflow/` 对应阶段产物中，便于审阅、回退和追踪。例如润色写入 `04-humanized.md`，格式清理写入 `05-format-cleaned.md`。
- `.thesis-workflow/` 内运行产物默认主动更新，但不对每次更新创建备份；重要确认版、主文件结构大改、用户原始材料变更和真实主文件修改才创建备份或快照。
- 多轮项目中，把输出格式、主文件路径、备份位置和已确认的文件生成授权记录到 project ledger 或 handoff。

### Skills 仓库维护文件

`tests/` 和 `evals/` 只用于维护 skills 仓库，不参与论文项目运行。修改脚本、规则 JSON、备份逻辑或输出路径策略时更新 `tests/`；修改 `SKILL.md` description、触发边界或工作流职责划分时更新 `evals/`。不要把这两个目录复制到论文项目的 `.thesis-workflow/` 中，也不要把论文项目运行产物写进它们。

### 备份协议

直接改论文主文件前按此顺序处理：

1. 确认目标是用户论文主文件，不是 skill 仓库内的 `SKILL.md` 或脚本。
2. 若目标文件在 Git 仓库中，先查看 `git status --short -- <file>` 并记录改前状态。
3. 无法使用 Git 分支备份时，复制一份到 `.thesis-workflow/backups/`，命名为 `<原文件名>.YYYYMMDD-HHMMSS.bak`，或使用用户指定的备份目录。
4. 修改完成后，将本轮结果另存到对应阶段产物，例如 `04-humanized.md` 或 `05-format-cleaned.md`；若是章节写作或证据补全，则更新 `02-chapter-draft.md` 或 `03-reference-audit.md`。
5. 在输出或 handoff 中报告主文件路径、备份路径、另存产物路径和复查命令结果。
6. 不清理备份文件，除非用户明确要求。

## 用户材料与标准规范

- 后续章节若依赖用户自己做出的内容，例如图纸、结构尺寸、实验记录、仿真截图、程序输出、设备选型、设计参数、现场照片或导师批注，应明确列入 `待用户补充的信息`，并向用户请求对应内容或文件。
- 不要根据常识补造用户未提供的实验数据、仿真结果、实物尺寸、性能指标或设计参数。
- 行业标准、国家标准、规范、规程、验收要求和限值不一定存在于用户 Zotero 文献库。需要此类依据时，先查本地文献和用户材料；不足时主动搜索官方标准平台、主管部门、标准发布机构、出版社页面或其他可靠来源。
- 已核验的标准规范应作为正式论文依据进入正文，用于支撑设计参数、限值、选型依据、验收要求或安全裕量。正文应说明标准名称、标准号、版本/年份和适用范围，并保留 `[参考文献]` 或学校模板要求的正式引用。
- 无法确认标准条文、版本、年份或适用范围时，不把对应要求写成定论；放入 `证据缺口清单` 并说明需要核验的标准名称、标准号、版本和条文范围。

## 确认问题

确认门只问当前必要问题，不要一次性问完所有问题。

可使用这些模板：

- 初始输出格式：“请确认输出格式：直接在对话中给出 Markdown，还是生成 `.md`/`.docx` 文件？未指定时我默认用对话 Markdown。”
- 论文主文件：“请确认论文主文件路径。若项目中已有明确的 `main.tex`、`thesis.tex`、`.docx` 或 `.md` 主文件，我将使用该文件；仍无法判断时再由你指定。”
- 总大纲确认：“请确认是否按此总大纲进入第 X 章细纲；如需调整，请指出章节或研究重点。”
- 细纲确认：“请确认本章细纲是否可以进入正文写作；如需调整，请指出需要增删的段落或图表。”
- 证据缺口：“以下内容缺少来源。请提供材料，或允许我改为网络检索/降级表述。”
- 真实主文件修改：“请确认是否直接修改论文主文件。确认后我会先备份原文件，再写回主文件，并把本轮结果另存到 `.thesis-workflow/` 对应阶段产物。”

## 输出默认值

- 独立一次性问答默认输出为对话 Markdown。
- 真实论文工作流默认主动创建或更新 `.thesis-workflow/` 运行产物；大纲、细纲和 P0/P1 处理方案仍需内容确认后才能进入下游。
- 草稿和中间审阅产物优先用 `.md`，且默认合并到 `.thesis-workflow/` 内的一个主文件中。
- `.docx` 只在内容和格式要求稳定后生成。

## Project Ledger

多轮 thesis 项目中，建议维护专用 project ledger，记录已确认事实、来源、公式、参数、设计决策和待补证据。具体规则遵循 `references/project-ledger-rules.md`。

不要把项目特定事实、公式或数据写进 skill 文件夹。Skills 只保存可复用工作流规则。

## Source Policy

遵循 `references/source-policy.md`。

核心规则：不能为了推动流程而发明看似有来源的 claim。unsupported facts、parameters、formulas 和 conclusions 不进入正文；应放入 `未写入正文的待补资料`、`证据缺口清单` 或 project ledger，或向用户索要材料。
