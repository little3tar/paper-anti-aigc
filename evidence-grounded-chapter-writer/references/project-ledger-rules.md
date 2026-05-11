# Project Ledger Rules

Default location: `.thesis-workflow/project-ledger.md` in the thesis project root. Do not create or update a project ledger inside the reusable skill directory.

For multi-chapter thesis work, use project ledger files to preserve confirmed information across sessions. These files belong in the user's thesis workspace, not in the skill directory. In an active thesis workflow, read the ledger before drafting and update it after drafting when confirmed facts, formulas, data, decisions, sources, or evidence gaps change.

Default location:

```text
.thesis-workflow/project-ledger.md
```

Large projects may split the same sections into:

```text
.thesis-workflow/ledger/
  facts.md
  formulas.md
  sources.md
  decisions.md
  figures-tables.md
  chapter-status.md
```

Read existing ledger files before drafting. When drafting produces new confirmed facts, formulas, data, decisions, sources, or evidence gaps, update `.thesis-workflow/project-ledger.md` if the workflow directory already exists or the user has asked to run the thesis workflow. Ask only when the thesis project root or the user's willingness to keep workflow files is unclear.

Use `draft`, `needs-source`, or `needs-user-data` for unconfirmed items. Do not turn unconfirmed material into confirmed ledger facts merely because it was useful for drafting.

Use these status labels:

- `confirmed`
- `draft`
- `needs-source`
- `needs-user-data`
- `derived`
- `superseded`

Do not overwrite confirmed entries silently. If a parameter, formula, or decision changes, keep the old entry and mark it `superseded`.
