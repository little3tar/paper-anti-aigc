# Project Ledger Rules

For multi-chapter thesis work, use project ledger files to preserve confirmed information across sessions. These files belong in the user's thesis workspace, not in the skill directory.

Recommended location:

```text
thesis-work/
  facts.md
  formulas.md
  sources.md
  decisions.md
  figures-tables.md
  chapter-status.md
```

Read existing ledger files before drafting. When drafting produces new confirmed facts, formulas, data, or decisions, propose ledger updates in the handoff. Edit the files only if the user asked for file updates or has already approved maintaining the ledger.

Use these status labels:

- `confirmed`
- `draft`
- `needs-source`
- `needs-user-data`
- `derived`
- `superseded`

Do not overwrite confirmed entries silently. If a parameter, formula, or decision changes, keep the old entry and mark it `superseded`.
