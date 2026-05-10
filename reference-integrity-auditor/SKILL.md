---
name: reference-integrity-auditor
description: Audit Chinese engineering thesis drafts for unsupported claims, weak citations, fabricated-looking literature, missing evidence, citation keyword consistency, and source reliability. Use after chapter drafting and before polishing, humanizing, format cleanup, or final bibliography work.
---

# Reference Integrity Auditor

Use this skill to check whether a thesis outline, chapter draft, or section draft is actually supported by sources. It should run before style polishing so the text does not become more fluent while remaining weakly sourced.

## Workflow

1. Identify the audit scope.
   - Determine whether the user wants paragraph-level audit, citation-key audit, source-list audit, or a revision-ready issue list.
   - If output format is unspecified, default to a Markdown audit report in chat.
   - If project ledger files exist, read them and check the draft against confirmed facts, formulas, sources, and decisions.

2. Segment the draft.
   - Split by headings and paragraphs.
   - Preserve formulas, figure placeholders, tables, and citation placeholders.
   - Do not rewrite the whole chapter unless the user asks for edits.

3. Check source support.
   - Every paragraph with factual or technical claims should have a source marker, user-provided data marker, design assumption, formula derivation, or clear internal reasoning.
   - Flag unsupported quantities, performance comparisons, equipment specifications, standards, named technologies, and research-status claims.
   - Flag vague source phrases such as "研究表明" when no source is attached.
   - For formulas and calculations, verify that original parameters have sources and derived parameters have reproducible calculation chains.

4. Check formula and calculation integrity.
   - Read `references/formula-audit-rules.md` for detailed criteria.
   - Read `references/project-ledger-audit-rules.md` when the project uses ledger files.
   - Preserve formulas exactly during audit unless the user asks for correction.
   - Check formula source, symbol definitions, units, substitution steps, result precision, and selection margin.
   - Flag any calculation result that cannot be reproduced from the preceding parameters.

5. Check citation keyword integrity.
   - Verify `[参考文献]`, `[引用关键词: ...]`, `[网络资料: ...]`, and `[待补来源: ...]` are used consistently.
   - Ensure Chinese titles are preserved and English keys are lowercase without spaces or punctuation when keys are present.
   - Flag duplicate English keys unless year or first author disambiguates them.

6. Classify findings.
   - `P0`: likely fabricated or materially false claim.
   - `P1`: important claim lacks source or has source mismatch.
   - `P2`: citation marker exists but is too vague to resolve.
   - `P3`: style or consistency issue that can wait until formatting.

7. Recommend next action.
   - If P0/P1 issues remain, fix evidence before polishing.
   - If only P2/P3 issues remain, proceed to `engineering-paper-humanizer`, then `academic-format-cleaner`.

## Audit Output

Return findings first. Use this structure:

1. `主要问题`
2. `逐段证据审查表`
3. `公式与计算审查表`
4. `引用关键词与来源清单问题`
5. `需要补充的资料`
6. `可直接进入后处理的部分`
7. `建议的下一步确认问题`

Do not invent missing sources. When a source is needed, describe the evidence type and likely search keyword instead of fabricating a reference.
