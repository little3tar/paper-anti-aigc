# Formula And Calculation Audit Rules

Use this checklist when auditing engineering thesis chapters with formulas, parameters, or calculations.

## Audit Checklist

For each formula block or calculation sequence, check:

1. Formula purpose is stated.
2. Formula source is cited or derivation is shown.
3. Every symbol is defined.
4. Units are provided for physical quantities.
5. Original parameters have source markers.
6. Design assumptions are marked as assumptions.
7. Substitution process is shown for key results.
8. Result can be reproduced from preceding values.
9. Unit conversion is explicit.
10. Component selection includes margin or rated-capacity check.

## Severity

- P0: formula or result contradicts stated values, or appears fabricated.
- P1: key result lacks formula, source value, or reproducible substitution.
- P2: symbol/unit/source marker is incomplete but result is probably recoverable.
- P3: formatting issue such as inconsistent equation numbering or table style.

## Red Flags

- A result is given directly after qualitative text with no formula.
- A parameter appears in a table but has no source type.
- The same symbol means different things in adjacent sections.
- Unit conversion changes magnitude without explanation.
- Selection conclusion says "满足要求" but no rated pressure, rated flow, safety factor, or margin is shown.
- Literature claims and author conclusions are mixed without clear boundary.

## Audit Output Table

Use this table when possible:

| Location | Formula/parameter | Problem | Severity | Required fix |
| --- | --- | --- | --- | --- |

Do not silently correct formulas unless asked. When correction is necessary, show the original problem and the corrected calculation chain.
