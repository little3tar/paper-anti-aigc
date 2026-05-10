# Project Ledger Rules

Use a project ledger for long thesis projects where confirmed facts, data, formulas, sources, and decisions must survive across chapters and agent sessions.

## Location

Do not write project-specific data into skill folders. Store it in the user's thesis workspace after confirmation, for example:

```text
thesis-work/
  facts.md
  formulas.md
  sources.md
  decisions.md
  figures-tables.md
  chapter-status.md
```

If the user does not want files, keep the same sections in the chat handoff.

## When To Ask

Ask before creating ledger files:

"是否创建 `thesis-work/` 台账文件，用于保存已确认的内容、数据、公式、来源和章节状态？"

If files already exist, read them before planning or drafting and update only after the user asks or confirms.

## Ledger Contents

### `facts.md`

Confirmed task requirements, object descriptions, known constraints, terminology, and user-approved statements.

Recommended columns:

| ID | Fact | Type | Source | Status | Notes |
| --- | --- | --- | --- | --- | --- |

### `formulas.md`

Confirmed formulas, symbol definitions, assumptions, and derivation notes.

Recommended columns:

| ID | Formula | Purpose | Symbols | Source | Applies to | Status |
| --- | --- | --- | --- | --- | --- | --- |

### `sources.md`

Zotero/local/web/user sources and citation keys.

Recommended columns:

| Key | Title | Authors/Year | Source type | Search keyword | Used in | Notes |
| --- | --- | --- | --- | --- | --- | --- |

### `decisions.md`

User-approved outline choices, design choices, terminology choices, and output format decisions.

Recommended columns:

| Date | Decision | Reason | Scope | Open issues |
| --- | --- | --- | --- | --- |

### `figures-tables.md`

Planned figures, tables, required data, and generation status.

Recommended columns:

| ID | Placeholder | Needed content | Source/data | Target chapter | Status |
| --- | --- | --- | --- | --- | --- |

### `chapter-status.md`

Chapter-level status.

Recommended columns:

| Chapter | Outline | Evidence | Draft | Audit | Humanize | Format | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Status Labels

Use these labels:

- `confirmed`
- `draft`
- `needs-source`
- `needs-user-data`
- `derived`
- `superseded`

Never overwrite confirmed data silently. Add a new row or mark the old row as `superseded`.
