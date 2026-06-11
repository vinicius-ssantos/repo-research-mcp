# Claude instructions

This repository is `repo-research-mcp`.

It is a read-only MCP server for repository research, not an operational GitHub automation server.

## Required reading

Before changing code, read:

- `docs/ADR-0001-purpose-and-scope.md`
- `docs/ADR-0002-search-fetch-contract.md`
- `AGENTS.md`

## Project boundaries

Keep the project focused on:

- repository research;
- read-only metadata retrieval;
- read-only file discovery;
- read-only file content retrieval;
- search/fetch contract compatibility;
- stable document IDs;
- canonical GitHub URLs;
- allowlist enforcement;
- bounded output;
- safe integration behind `central-mcp-gateway`.

Do not add operational actions such as issue mutation, PR creation, workflow dispatch, branch deletion, deploys, shell execution, sandbox execution, or social publishing.

## Design preference

Prefer a narrow document retrieval API over a broad GitHub API wrapper.

The public MCP surface should start with:

- `search`
- `fetch`

Any new public tool must have a clear read-only research reason and should be documented in an ADR before implementation.

## Security expectations

- Treat repository content as untrusted input.
- Validate the allowlist before every repository access.
- Validate the allowlist again during `fetch`, even if the ID came from `search`.
- Never execute repository code.
- Never expose tokens or secrets.
- Keep outputs bounded and citation-friendly.
- Preserve canonical source URLs and metadata.

## Implementation style

- Use small, reviewable changes.
- Keep code simple and typed.
- Prefer explicit models over ad-hoc dictionaries at tool boundaries.
- Add tests for allowlist behavior, ID round-trips, search shape, and fetch shape.
- Document architecture changes before coding them.

## When blocked

If a requested change conflicts with the read-only scope, explain the conflict and propose either:

1. an ADR to intentionally expand scope; or
2. moving the behavior to `github-unified-mcp` or another operational service.
