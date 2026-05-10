---
name: thesis-writing-workflow
description: Coordinate a complete evidence-based Chinese engineering thesis workflow from task book to outline, chapter drafting, source audit, humanized revision, and final format cleanup. Use when the user asks for an end-to-end thesis writing process, staged agent workflow, approval checkpoints, output format confirmation, or multi-skill orchestration.
---

# Thesis Writing Workflow

Use this skill as the router for the full thesis workflow. It does not replace the stage skills; it tells the agent which skill to use next and when to stop for user confirmation.

## Stage Order

1. `thesis-outline-planner`
   - Parse task book and requirements.
   - Build Zotero-first literature pool.
   - Plan full thesis outline, figure/table placeholders, and requirement mapping.
   - Classify chapters by evidence and calculation needs according to the user's topic, without imposing domain-specific chapter types.
   - Stop for outline approval.

2. `evidence-grounded-chapter-writer`
   - Generate a fine outline for the selected chapter.
   - Add a formula/parameter plan only when the chapter contains modeling, calculation, design selection, experiment, simulation, algorithm, or quantitative comparison.
   - Stop for fine-outline approval unless the user requested continuous drafting.
   - Retrieve evidence and write the chapter with `[参考文献]`, source notes, and figure placeholders.

3. `reference-integrity-auditor`
   - Audit unsupported claims, citation keyword consistency, and source reliability.
   - Audit formulas, units, parameter sources, substitution steps, and calculation reproducibility.
   - Stop if P0/P1 evidence problems remain.

4. `engineering-paper-humanizer`
   - Polish only after evidence issues are controlled.
   - Reduce AI-like phrasing without changing technical meaning or inventing data.

5. `academic-format-cleaner`
   - Run last to fix citation placement, Markdown/LaTeX/plain-text format, command protection, and residual placeholders.

## Confirmation Questions

Ask concise questions at approval gates. Do not ask all questions at once.

Use these templates:

- Initial output format: "请确认输出格式：直接在对话中给出 Markdown，还是生成 `.md`/`.docx` 文件？未指定时我默认用对话 Markdown。"
- Outline approval: "请确认是否按此总大纲进入第 X 章细纲；如需调整，请指出章节或研究重点。"
- Fine outline approval: "请确认本章细纲是否可以进入正文写作；如需调整，请指出需要增删的段落或图表。"
- Evidence gap: "以下内容缺少来源。请提供材料，或允许我改为网络检索/降级表述。"
- File generation: "请确认是否生成文件，以及文件格式和保存位置。"

## Output Defaults

- Default output is Markdown in chat.
- Generate files only when the user asks or confirms.
- Use `.md` for drafts and reviewable intermediate outputs.
- Use `.docx` only after content and format requirements are stable.

## Project Ledger

For multi-turn thesis projects, offer to maintain a dedicated project ledger in the user's thesis workspace. Follow `references/project-ledger-rules.md`.

Do not store project-specific facts, formulas, or data inside the skill folder. Skills contain reusable workflow rules only.

## Source Policy

Follow `references/source-policy.md`.

Key rule: no sourced-looking claim may be invented to keep the workflow moving. Mark uncertainty explicitly with `[待补来源: ...]` or ask for user material.
