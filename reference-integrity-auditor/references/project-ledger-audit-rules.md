# Project Ledger Audit Rules

Use this when a thesis project keeps ledger files such as `facts.md`, `formulas.md`, `sources.md`, `decisions.md`, `figures-tables.md`, and `chapter-status.md`.

## Audit Against Ledger

Check the draft against confirmed ledger entries:

- Facts in the draft should not contradict `facts.md`.
- Formulas, symbols, assumptions, and scope should match `formulas.md`.
- Citation placeholders and source notes should be resolvable in `sources.md` when the source is already known.
- Chapter structure and approved choices should match `decisions.md`.
- Figure/table placeholders should match `figures-tables.md` or be added as proposed updates.

## Finding Types

- `ledger-missing`: the draft introduces a new fact, parameter, formula, or source that should be added to the ledger.
- `ledger-conflict`: the draft contradicts a confirmed ledger entry.
- `ledger-stale`: the ledger contains a superseded value still used in the draft.
- `ledger-unresolved`: the draft relies on an entry marked `needs-source` or `needs-user-data`.

## Rule

Do not silently update confirmed ledger entries during audit. Report proposed changes and ask for confirmation unless the user explicitly requested direct file edits.
