---
name: thesis-outline-planner
description: Plan evidence-based Chinese engineering thesis outlines from task books, design requirements, research proposals, or advisor instructions. Use when the user wants to turn a thesis topic into a full chapter structure, literature-backed writing workflow, task-to-chapter mapping, figure/table plan, or staged approval process before drafting.
---

# Thesis Outline Planner

Use this skill to convert a thesis task book or design brief into a sourced, reviewable thesis plan. It is the first skill in the thesis workflow and should run before chapter drafting.

## Workflow

1. Parse the user's task source.
   - Extract research object, design tasks, required deliverables, methods, constraints, and named reference systems such as JOY MC51.
   - Preserve user-provided wording for formal requirements.
   - If essential information is missing, ask only the minimum confirmation question.

2. Confirm output format when it is not specified.
   - Default to direct Markdown in chat.
   - Ask a concise question only when the delivery format affects the work: "请确认输出格式：直接在对话中给出 Markdown，还是生成 `.md`/`.docx` 文件？"
   - If the user wants a Word document, use the document/docx skill after the plan is approved.

3. Build a literature pool.
   - Prefer Zotero MCP or any local literature MCP/resource exposed in the environment.
   - If no Zotero MCP is available, check for other local resources, exported `.bib`/`.ris`/`.csv` files, or user-supplied literature lists.
   - If no local literature source is available, use web search only for the missing topics.
   - Target at least 50 relevant references for the whole thesis plan when the topic is broad enough. Do not force 50 references for a narrow subtask.
   - Track each source with title, author/year if available, source type, search keyword, and usable thesis section.

4. Create the outline.
   - Produce the full chapter structure, section-level content, and chapter logic.
   - Map every user requirement to one or more chapters.
   - Include suggested methods, simulations, calculations, experiments, algorithms, diagrams, and appendices.
   - Mark the expected evidence type for each chapter: literature review, design reasoning, formula/calculation, data analysis, experiment/simulation, algorithm/modeling, or document-only description. Do not impose domain-specific formula topics unless the user's task requires them.
   - Include figure/table placeholders using the exact format `[此处插入图片：...]`.

5. Ask for approval before chapter drafting.
   - End with a clear confirmation question: "请确认是否按此总大纲进入第 X 章细纲设计；如需调整，请指出章节、研究重点或输出格式。"
   - Do not proceed to full chapter writing unless the user has already requested it.
   - For long projects, ask whether to create or update a project ledger for confirmed facts, sources, formulas, and decisions.

## Evidence Rules

Read `references/evidence-rules.md` when the task involves literature retrieval, citation keyword design, or source fallback decisions.

Use these source labels during planning:

- Zotero or local library source: `[引用关键词: 检索词]`
- Web source: `[网络资料: 检索词或网页标题]`
- User-provided source: `[用户材料: 文件名或材料名]`
- Missing source: `[待补来源: 需要补充的证据类型]`

Never invent equipment parameters, performance claims, standards, experiment results, or named literature. If a claim is plausible but not sourced, mark it as pending evidence or rewrite it as a design assumption.

## Recommended Output

Use this structure unless the user specifies another format:

1. `任务理解`
2. `资料检索计划与文献池`
3. `论文总章节规划`
4. `任务书要求与章节对应关系`
5. `建议图表与附录`
6. `公式/数据/证据需求判断`
7. `项目台账建议`
8. `待确认问题`
9. `下一步建议`

Keep the plan concrete enough for a later agent to execute chapter writing without reinterpreting the topic.
