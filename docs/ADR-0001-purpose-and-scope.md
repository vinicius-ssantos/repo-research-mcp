# ADR-0001: Purpose and scope

## Status

Accepted

## Context

`repo-research-mcp` exists to expose repository knowledge to research-oriented clients in a safe and narrow way.

The broader platform already has operational MCPs for GitHub automation, deploy orchestration, sandbox execution, social publishing, and creative workflows. Those capabilities are useful, but they are not appropriate for a research-only surface, especially when the client is expected to browse repository information, summarize architecture, compare files, or support Deep Research-style workflows.

## Decision

This project is a read-only MCP server focused on repository research.

The initial public contract is limited to:

- `search`: find relevant repository documents and return compact, citable results.
- `fetch`: retrieve one document returned by `search`, including canonical URL, text, and metadata.

All access must be constrained by an allowlist of repositories.

## In scope

- Repository metadata retrieval.
- File discovery.
- File content retrieval.
- Code/document search.
- Architecture review support.
- Stable document identifiers for search/fetch round-trips.
- Canonical GitHub URLs for citations.
- Read-only audit-friendly behavior.
- Integration behind `central-mcp-gateway` as a research-only upstream.

## Out of scope

This server must not:

- create issues;
- update issues;
- open pull requests;
- merge pull requests;
- delete branches;
- dispatch workflows;
- deploy services;
- execute shell commands;
- access sandbox execution;
- publish social or external content;
- perform paid operations.

Operational repository actions belong to `github-unified-mcp` or a future dedicated operational API, not to this service.

## Security constraints

- Deny by default.
- Allowlist-only repository access.
- Prefer read-only GitHub tokens.
- Do not expose secrets in responses.
- Do not execute repository code.
- Preserve source URLs and metadata.
- Keep tool output bounded.
- Treat repository content as untrusted input.

## Consequences

The project intentionally duplicates a small subset of repository read behavior instead of exposing a full GitHub automation MCP to research clients.

This makes the research surface easier to reason about, easier to audit, and safer to connect to tools like ChatGPT Deep Research.
