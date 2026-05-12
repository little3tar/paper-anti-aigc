# Formula And Calculation Rules

Use these rules for technical thesis chapters that contain formulas, parameters, modeling, derivation, quantitative design, experiment/simulation data, algorithms, optimization, verification, or performance calculation.

## Formula Format

Use LaTeX math as the single source format:

- Inline formula: `$p=F/A$`
- Display formula: `\begin{equation} ... \end{equation}`
- Multi-line derivation: `\begin{align} ... \end{align}`

Prefer standard LaTeX syntax that transfers well to Markdown, LaTeX, and Word/MathType:

- Use `\frac{}`, `\sqrt{}`, `^`, `_`, `\mathrm{}`, `\cdot`, `\times`, Greek letters, and `align`.
- Avoid custom macros, package-specific commands, or complex formatting commands unless the target document requires them.
- Keep equation labels stable if using LaTeX, for example `\label{eq:pump-flow}`.

## Engineering Calculation Chain

For each important calculation, write in this order:

1. State the design objective or calculation purpose.
2. Give the formula and cite its source if it is not derived in the thesis.
3. Define every symbol after the formula.
4. Provide a parameter table.
5. Substitute values with units.
6. Give the result with reasonable precision.
7. Check unit consistency.
8. State the engineering margin or selection conclusion.

## Parameter Source Types

Every original parameter must be classified:

| Source type | Marker | Examples |
| --- | --- | --- |
| Literature | `[参考文献]` plus `[文献题名]` source note | empirical coefficient, material property, published equation |
| Verified standard/specification | `[参考文献]` plus standard name/number/version in body; working note may use `[标准规范: 标准号或规范名称]` | limit value, design code, acceptance requirement, recommended pressure |
| User task material | `[用户材料: ...]` | design requirement, target value, boundary condition |
| Manufacturer sample/manual | `[网络资料: ...]` or `[参考文献]` | rated parameter, product limit, catalog value |
| Design assumption | `[设计假设: ...]` | safety factor, initial value, simplification |
| Derived calculation | `[计算导出: 公式编号]` | area, torque, power, efficiency, index value |
| Simulation/experiment | `[仿真结果: 软件/工况]` or `[实验结果: ...]` | response, error, fluctuation, measured metric |

Do not present a design assumption as a measured fact. Do not present a derived value without the formula and source values. Do not write a standard requirement as a final design basis until the standard number, version/year, issuing body, and applicable clause or scope are verified.

## Standards In Body Text

Verified standards and specifications should be integrated into the thesis body when they support design parameters, limit values, selection basis, acceptance requirements, or safety margins. The sentence should name the standard, standard number, version/year, and applicable scope or clause when available, and keep a formal citation placeholder such as `[参考文献]`.

Use `[标准规范: ...]` as a working note while drafting or auditing. Before final cleanup, either convert it into a formal citation-supported sentence or move it to `证据缺口清单` if the standard remains unverified.

## Symbol Table

After important formulas, include or update a symbol table:

| Symbol | Meaning | Unit | Value | Source |
| --- | --- | --- | --- | --- |

Use consistent symbols across the chapter. If a symbol changes meaning between sections, rename it.

## Data Integrity

- Preserve all source values exactly unless unit conversion is explicitly shown.
- Use SI units by default and state conversions.
- Keep effective figures reasonable for engineering design.
- If a numeric value has no source, keep it out of the body and record the missing parameter in `未写入正文的待补资料` or the project ledger.
- If a formula is standard but no source is available, keep it as a formula plan outside the final body until the source or derivation basis is supplied.

## Formula Need Classification

Do not assume that a chapter needs formulas only because it is not the introduction. Classify sections by task:

- No formula required: purely narrative background, policy context, chapter organization, qualitative review.
- Formula optional: conceptual design, qualitative comparison, requirement decomposition.
- Formula recommended: performance index definition, method comparison, model description, data processing.
- Formula required: quantitative design, parameter calculation, model derivation, algorithm derivation, experiment/simulation analysis, optimization, verification, component or scheme selection with rated limits.

"Default mark" means marking the section's expected evidence/calculation needs in the fine outline. It does not mean inventing formulas in advance. For example, write "本节需要参数来源表和单位校核，具体公式待依据设计方案确定" rather than fabricating a calculation.
