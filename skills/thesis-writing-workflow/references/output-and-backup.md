# 输出与文件安全

## 输出规则

- 区分"内容确认"和"文件更新"。真实论文工作流中，`.thesis-workflow/` 内运行产物应随每次相关阶段运行主动创建或更新；但总大纲、章节细纲、P0/P1 处理方案和真实论文主文件修改仍需要用户确认。
- 单独运行任一 thesis skill 时也遵循同一规则：若当前目录、用户指定目录或已识别的论文项目根目录中存在 `.thesis-workflow/`，或用户明确处于论文 workflow 项目中，则该 skill 运行结束必须更新对应阶段产物和必要的 `ledger/` 文件；不要因为用户没有再次说"生成文件"而跳过更新。
- 用户只要求一次性在对话中返回内容，且没有进入论文项目工作流时，可以不创建文件；一旦创建或使用 `.thesis-workflow/`，后续阶段默认读取并更新其中的相关产物。
- 阶段开始前先读取已有上游产物。若 `.thesis-workflow/ledger/` 存在，读取其中的 facts/decisions/chapter-status；若 `main-tex-context.md` 存在，读取项目结构地图。若目标阶段依赖大纲、草稿或审计报告，也读取对应的 `outline.md`、`chapters/chX/draft.md` 或 `chapters/chX/audit.md`。
- 阶段结束后更新本阶段产物和 `ledger/` 对应文件（facts/decisions/chapter-status）。大纲阶段更新 `outline.md`、`literature-pool.md` 和 `main-tex-context.md`，章节写作阶段更新 `chapters/chX/draft.md` 和 `chapters/chX/detailed-outline.md`，证据审计阶段更新 `chapters/chX/audit.md` 和 `chapters/chX/status.json`，润色阶段更新 `chapters/chX/humanized.md`（操作记录）和 `chapters/chX/status.json`，格式清理阶段更新 `chapters/chX/format-cleaned.md`（操作记录）和 `chapters/chX/status.json`。
- `ledger/facts.md` 和 `ledger/decisions.md` 在确认新事实、参数、公式、来源、设计假设、用户材料或决策时更新。`ledger/chapter-status.md` 在每个阶段完成时更新。`main-tex-context.md` 只在论文主文件结构、章节标题、引用方案、模板或主文件路径变化时更新。
- 用户要求生成文件但未指定目录时，默认创建或使用论文项目根目录下的 `.thesis-workflow/`。如果当前工作目录位于 skill 仓库内，不能把运行产物写进 skill 仓库；应使用用户论文项目根目录，无法判断时先确认。
- 用户要求生成文件但未指定格式时，默认按章拆分输出 `main-chX.md` / `main-chX.txt` / `main-chX.tex`（每章一个独立文件）。如项目中已有明确的各章独立文件（如 `chapters/ch1.tex`），优先沿用现有命名。
- 论文真实主文件优先使用用户提供或项目中可明确识别的现有文件名；无法判断时先确认。若用户始终没有指定，按章使用 `main-chX.md` / `main-chX.txt` / `main-chX.tex`。
- 推荐运行产物默认文件名按任务选择：大纲为 `.thesis-workflow/outline.md`，章节写作产物按章归档为 `.thesis-workflow/chapters/chX/detailed-outline.md`、`.thesis-workflow/chapters/chX/draft.md`、`.thesis-workflow/chapters/chX/audit.md`、`.thesis-workflow/chapters/chX/status.json`、`.thesis-workflow/chapters/chX/humanized.md`、`.thesis-workflow/chapters/chX/format-cleaned.md`，不要把这些运行产物写进 skill 仓库。
- Project ledger 已拆分为 `ledger/` 子目录：`ledger/facts.md`（设计参数）、`ledger/decisions.md`（决策记录）、`ledger/chapter-status.md`（章节进展）、`ledger/questions.md`（待确认问题）。各 skill 直接读写对应文件，无需索引文件。
- 文献池独立文件：`.thesis-workflow/literature-pool.md`（文献全表，含 ZoteroKey 映射；分组原则见 outline-planner §建立文献池）。
- 章节细纲按章存放：`.thesis-workflow/chapters/chX/detailed-outline.md`（每章一份，段落级写作点）。大纲文件 `outline.md` 只保留到小节标题层级。
- 批量操作日志：`.thesis-workflow/operations-log.md`（项目检查、章节清除等一次性操作记录，只追加不修改）。
- Project ledger 放在 `ledger/` 子目录下，各 skill 直接读写对应文件。按 `references/main-tex-context-template.md` 生成的项目上下文默认放在 `.thesis-workflow/main-tex-context.md`，由 `thesis-outline-planner` 在确认输出格式后首次创建。后续各阶段读取其中的格式约定；当主文件结构、章节标题、引用方案、模板或主文件路径变化时，触发变更的阶段负责更新。
- 文献笔记缓存按章存储：`.thesis-workflow/chapters/chX/literature-notes.md`（随章保留，不自动清空）。
- 图表数据溯源清单默认放在 `.thesis-workflow/figure-data-manifest.md`（持久文件，数据文件路径、生成脚本、输出格式）。
- **生成图存放**：AI 根据 Mermaid 代码块、matplotlib 脚本、DOT 文件或提示词模板渲染产生的图片文件，统一存放在 `.thesis-workflow/generated-figures/`。命名格式 `Fig X-Y 描述.png`，与 manifest 中 Figure ID 对应。该目录与 `evidence/user-figures/` 分工明确——用户原始图片不放此处。规则见 chapter-writer 参考文件 `figure-data-manifest-rules.md`。
- **用户视频存放**：用户提供的视频、动画、演示录像存放在 `.thesis-workflow/evidence/user-videos/`。规则见 `references/user-material-protocol.md`。
- 计算记录默认放在 `.thesis-workflow/calculation-records.md`（计算底稿，正文数值的唯一权威数据源）。
- 每次直接修改用户论文主文件前，先通过 `scripts/git_snapshot.py <文件>` 创建备份。脚本优先使用 Git 分支备份，回退到 `.thesis-workflow/backups/` 下的文件复制备份。不要把备份写进 skill 仓库。备份对应章文件 `main-chX.md` / `main-chX.txt` / `main-chX.tex`。
- 直接修改真实论文主文件后，将本轮变更清单（改了什么、为什么改）写入 `.thesis-workflow/chapters/chX/` 对应阶段产物（`humanized.md` 或 `format-cleaned.md`）。这些产物是操作记录，不存全文副本——全文以主文件为唯一权威输出。
- `.thesis-workflow/` 内运行产物默认主动更新，但不对每次更新创建备份；重要确认版、主文件结构大改、用户原始材料变更和真实主文件修改才创建备份或快照。重大确认版本建议使用 `--anchor` 参数创建锚点备份，锚点备份永不自动淘汰。
- 以下 `.thesis-workflow/` 产物在关键节点应额外备份：`ledger/` 目录（每次确认后）、`outline.md`（总大纲确认后）、`chapters/chX/draft.md`（细纲确认后）。备份命令同主文件：`git_snapshot.py .thesis-workflow/outline.md --anchor`。
- 普通备份保留数量可通过 `GIT_SNAPSHOT_MAX_BACKUPS` 环境变量或 `--max-backups N` 参数调整。锚点备份不受此限制。
- 多轮项目中，把输出格式、主文件路径、备份位置和已确认的文件生成授权记录到 project ledger 或 handoff。

## Skills 仓库维护文件

`tests/` 和 `evals/` 只用于维护 skills 仓库，不参与论文项目运行。修改脚本、规则 JSON、备份逻辑或输出路径策略时更新 `tests/`；修改 `SKILL.md` description、触发边界或工作流职责划分时更新 `evals/`。不要把这两个目录复制到论文项目的 `.thesis-workflow/` 中，也不要把论文项目运行产物写进它们。

## 备份协议

备份由 `scripts/git_snapshot.py` 统一执行。

直接改论文主文件前按此顺序处理：

1. 确认目标是用户论文主文件，不是 skill 仓库内的 `SKILL.md` 或脚本。
2. 调用 `git_snapshot.py <文件>` 创建备份。脚本自动选择 Git 分支备份（仓库内）或文件复制备份（非 Git 目录）。
3. 备份文件名格式：文件模式为 `<原文件名>_YYYYMMDD-HHMMSS-NN.<扩展名>`（NN 为厘秒精度，由脚本自动生成）；Git 模式为 `backup/humanizer/YYYYMMDD-HHMMSS-NN` 分支。锚点备份在时间戳后附加 `-anchor` 标记。手动创建的备份建议沿用同格式并附加说明性后缀（如 `-r2` 表示第二轮修订）。
4. 修改完成后，将本轮结果另存到对应阶段产物，例如 `chapters/chX/humanized.md` 或 `chapters/chX/format-cleaned.md`；若是章节写作或证据补全，则更新 `chapters/chX/draft.md` 或 `chapters/chX/audit.md`。
5. 在输出或 handoff 中报告主文件路径、备份路径、另存产物路径和复查命令结果。
6. 超出数量限制的普通备份静默淘汰。锚点备份永不自动淘汰。手动清理所有备份（含锚点）使用 `git_snapshot.py --cleanup`。

重要确认版本（大纲确认、细纲确认、主文件结构大改、用户原始材料变更）建议使用 `--anchor` 创建锚点备份，确保不会被自动淘汰覆盖。
