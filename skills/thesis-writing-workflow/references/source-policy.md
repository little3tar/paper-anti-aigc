# Source Policy For Thesis Workflow

## Priority

1. Zotero MCP or local literature MCP.
2. User-supplied task books, notes, PDFs, exported reference files, and advisor comments.
3. Official documents, verified standards/specifications, patents, journal pages, manufacturer pages, and university repositories.
4. Web search results from reliable sources.

Treat standards and specifications as a separate source class. Industry standards, national standards, codes, procedures, acceptance requirements, and limit values are often absent from a user's Zotero library; when the thesis depends on them, actively search official standard platforms, regulator or ministry pages, standards publishers, professional associations, or other reliable sources.

Verified standards are formal thesis evidence. After verifying the standard name, number, version/year, issuing body, and applicable clause or scope, integrate the requirement into the thesis body as a design basis, parameter basis, acceptance basis, limit-value basis, or safety-margin basis, with a formal citation placeholder.

## Fallback Behavior

If Zotero MCP is unavailable:

1. Check whether another MCP/resource exposes local literature.
2. Ask whether the user can provide `.bib`, `.ris`, `.csv`, PDF folders, or reference lists when local-library accuracy is required.
3. Use web search for missing public facts only.
4. Use external search for standards/specifications when local literature does not contain the needed standard number, version, year, issuing body, or clause scope.

## Stop Conditions

Stop and ask the user when:

- The requested output format affects file creation or document tooling.
- The outline changes the thesis scope.
- A chapter depends on unavailable experimental data, dimensions, pressure/flow values, or advisor-specific requirements.
- A chapter depends on user-created materials such as drawings, measurements, experiment logs, simulation screenshots, program outputs, equipment selections, site photos, or advisor annotations.
- The draft contains P0/P1 evidence problems after audit.

If the user explicitly authorized preauthorized continuous mode, do not stop for output format or workflow artifact updates; record the assumed decisions in the handoff or project ledger. Still stop for missing user-created data, unverifiable standards required for a final conclusion, unresolved P0/P1 issues in real submission work, and direct modification of a real thesis main file unless that modification was explicitly preauthorized.

## Evidence Gap Handling

Unsupported facts, parameters, formulas, standards, performance claims, and conclusions do not belong in the thesis body. Record them in `未写入正文的待补资料`, `证据缺口清单`, or the project ledger with the needed evidence type and likely source path. Write them into the body only after they are supported by local/Zotero evidence, user-provided material, confirmed design assumptions, verified standards/specifications, or reproducible derivation.

For unverified standards/specifications, record the needed standard name, candidate standard number, issuing body, year/version, clause range, and search source. Do not cite a standard as authoritative until the version and applicability are verified.
