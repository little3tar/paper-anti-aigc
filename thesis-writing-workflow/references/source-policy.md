# Source Policy For Thesis Workflow

## Priority

1. Zotero MCP or local literature MCP.
2. User-supplied task books, notes, PDFs, exported reference files, and advisor comments.
3. Official documents, standards, patents, journal pages, manufacturer pages, and university repositories.
4. Web search results from reliable sources.

## Fallback Behavior

If Zotero MCP is unavailable:

1. Check whether another MCP/resource exposes local literature.
2. Ask whether the user can provide `.bib`, `.ris`, `.csv`, PDF folders, or reference lists when local-library accuracy is required.
3. Use web search for missing public facts only.

## Stop Conditions

Stop and ask the user when:

- The requested output format affects file creation or document tooling.
- The outline changes the thesis scope.
- A chapter depends on unavailable experimental data, dimensions, pressure/flow values, or advisor-specific requirements.
- The draft contains P0/P1 evidence problems after audit.
