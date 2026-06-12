# repo-research-mcp

Read-only MCP server for repository research.

`repo-research-mcp` exposes a narrow, citation-friendly repository research surface for clients that need to search and fetch repository knowledge without receiving operational GitHub permissions.

The intended deployment path is behind `central-mcp-gateway` as a research-only upstream.

## Purpose

The project exists to answer repository research questions safely:

- find relevant files and documentation;
- fetch source documents by stable IDs;
- preserve canonical GitHub URLs;
- provide metadata useful for citations;
- support architecture and codebase analysis;
- keep all access read-only and allowlist-bound.

## Public contract

The initial MCP surface is limited to:

- `search(query, repository, limit)`
- `fetch(id)`

This is intentionally a document retrieval contract, not a broad GitHub automation API.

## Non-goals

This service must not create issues, update issues, open pull requests, merge pull requests, delete branches, dispatch workflows, deploy services, execute shell commands, access sandbox execution, publish social content, or perform paid operations.

Operational actions belong in other services such as `github-unified-mcp`, not here.

## Documentation

Start here:

- `docs/ADR-0001-purpose-and-scope.md`
- `docs/ADR-0002-search-fetch-contract.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/SECURITY.md`
- `AGENTS.md`
- `CLAUDE.md`

## Current status

The repository is in bootstrap phase.

Implemented so far:

- project configuration;
- typed response models;
- repository allowlist helper;
- stable document ID helper;
- research service placeholder;
- scope, architecture, roadmap, security, and agent guidance docs.

## Development

Install in editable mode with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run checks:

```bash
ruff check .
mypy src tests
pytest
```

## Security posture

- Deny by default.
- Enforce repository allowlist before every repository access.
- Re-check allowlist during fetch.
- Treat repository content as untrusted input.
- Never execute repository code.
- Never expose tokens or secrets.
- Keep tool output bounded.
