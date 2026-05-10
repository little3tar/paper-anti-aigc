---
name: evidence-grounded-chapter-writer
description: Write evidence-grounded Chinese engineering thesis chapters from an approved outline. Use when the user asks to draft, expand, or revise a specific thesis chapter or section with Zotero-first literature retrieval, citation placeholders, figure placeholders, source lists, and approval checkpoints.
---

# Evidence Grounded Chapter Writer

Use this skill after a thesis outline or chapter target has been agreed. It turns one chapter or section into a sourced draft without inventing facts.

## Workflow

1. Confirm the writing target.
   - Identify chapter number, section range, expected length, citation style, and output format.
   - If output format is unspecified, default to Markdown in chat.
   - Ask only when necessary: "请确认本章输出格式：直接对话 Markdown、`.md` 文件，还是 `.docx` 文件？"
   - If a project ledger exists, read it before drafting. If no ledger exists and the work will span multiple chapters, ask whether to create one.

2. Produce a chapter fine outline for approval.
   - Break the chapter into sections and paragraph-level writing points.
   - Mark which points require literature support, formulas, design assumptions, figures, tables, or user-supplied data.
   - For any section involving modeling, calculation, design selection, experiment/simulation, algorithm, or quantitative comparison, mark the expected formula/parameter work. Do not invent formula topics before the user's topic and evidence require them.
   - Ask for approval before full drafting unless the user explicitly asked to continue without review.

3. Retrieve evidence.
   - Prefer Zotero MCP or local literature MCP.
   - If unavailable, inspect other local literature exports or ask the user to provide exported references when local evidence is required.
   - Use web search only for gaps and only from reliable sources.
   - Build a small evidence table for the target chapter before drafting.

4. Draft the chapter.
   - Write in Chinese engineering thesis style.
   - Insert `[参考文献]` at positions that need formal citation in the final document.
   - Preserve citation keyword notes near the draft or in a source table so later bibliography work can resolve them.
   - Use `[此处插入图片：...]` for figures that should be drawn or inserted later.
   - Use LaTeX math as the single source format for formulas so the draft can move between Markdown, LaTeX, and Word/MathType workflows.
   - For engineering calculation sections, write the chain as formula, symbol table, parameter source table, substitution, result, unit check, and design margin.
   - Do not add unsupported quantitative claims, equipment parameters, experimental conclusions, or literature attributions.
   - When new facts, parameters, formulas, or design decisions become confirmed, propose updates to the project ledger instead of scattering them only in chat.

5. Finish with a chapter handoff.
   - Provide source list, unsupported items, required user data, and recommended next step.
   - Recommend `reference-integrity-auditor` before any polishing.
   - After evidence audit, use `engineering-paper-humanizer`, then `academic-format-cleaner`.

## Citation Keyword Rules

Read `references/citation-key-rules.md` when generating reference placeholders or source tables.

Read `references/formula-calculation-rules.md` when drafting any chapter that includes formulas, parameters, modeling, derivation, calculation, design selection, experiment/simulation data, algorithms, or quantitative comparison.

Read `references/project-ledger-rules.md` when using or updating confirmed project facts, formulas, source lists, or design decisions.

Use these working markers:

- In正文 formal placeholder: `[参考文献]`
- Source note for Zotero/local sources: `[引用关键词: 检索词]`
- Source note for network sources: `[网络资料: 检索词或网页标题]`
- Missing evidence: `[待补来源: 需要补充的证据类型]`

For reference titles:

- Chinese titles keep the original title.
- English titles use lowercase and remove spaces and punctuation.
- If duplicate keys appear, append year or first author, for example `mechanicalcuttingofhardrock2021`.

## Output Template

For a full chapter draft, return:

1. `章节细纲`
2. `证据表`
3. `公式与参数计划`
4. `正文初稿`
5. `图片与表格占位符清单`
6. `参考来源清单`
7. `待用户补充的信息`
8. `后处理建议`

For a user-approved direct draft, omit the approval pause but still include evidence and pending-source notes.
