# Project Ledger Rules

Default location: `.thesis-workflow/project-ledger.md` in the thesis project root. Do not create or update a project ledger inside the reusable skill directory.

Use a project ledger for long thesis projects where confirmed facts, data, formulas, sources, and decisions must survive across chapters and agent sessions. In an active thesis workflow, the ledger is a normal running artifact: read it at the start of each stage and update it at the end when the stage changes confirmed information or open evidence gaps.

## Location

Do not write project-specific data into skill folders. Store it in the user's thesis workspace. The default is one file:

```text
.thesis-workflow/
  project-ledger.md
```

If the project becomes too large, the same sections may be split into separate files under `.thesis-workflow/ledger/`, for example:

```text
.thesis-workflow/ledger/
  facts.md
  formulas.md
  sources.md
  decisions.md
  figures-tables.md
  chapter-status.md
```

If the user does not want files, keep the same sections in the chat handoff.

## When To Ask

Ask only when the thesis project root or the user's willingness to keep workflow files is unclear. If `.thesis-workflow/` already exists, or the user has asked to run the thesis workflow, create or update `.thesis-workflow/project-ledger.md` without a separate confirmation prompt.

When a confirmation is needed, ask:

"是否创建 `.thesis-workflow/project-ledger.md`，用于保存已确认的内容、数据、公式、来源和章节状态？"

If the user has explicitly preauthorized confirmations or file generation, create the ledger and record the authorization in `decisions.md` or the handoff report instead of asking again.

If files already exist, read them before planning, drafting, auditing, humanizing, or format cleanup. Update them after each relevant stage; use `draft`, `needs-source`, or `needs-user-data` for unconfirmed items instead of presenting them as confirmed facts.

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

Zotero/local/web/user sources and title-based source markers.

Recommended columns:

| Marker | Title | Authors/Year | Source type | Search keyword | Used in | Notes |
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
