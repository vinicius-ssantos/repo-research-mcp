# repo-research-mcp

Read-only MCP server for repository research, code search, file retrieval, architecture review, and Deep Research-compatible `search`/`fetch` over allowed GitHub repositories.

## Purpose

This project exposes repository knowledge safely to research-oriented clients.
It is intentionally read-only: it can search and fetch repository content, but it must not create issues, open pull requests, dispatch workflows, deploy services, run shell commands, or publish external content.

## Initial tools

- `search`: find relevant repository documents and return compact, citable results.
- `fetch`: retrieve a document returned by `search` with canonical URL and metadata.

## Security model

- Allowlist-only repository access.
- Read-only GitHub token expected in production.
- Stable document identifiers.
- Canonical GitHub URLs for citation.
- No write operations.
- No sandbox execution.
- No deploy/social/publication tools.

## Intended architecture

```text
ChatGPT Deep Research
        ↓
central-mcp-gateway
        ↓
repo-research-mcp
        ↓
GitHub API / repository index
```

## Status

Bootstrap in progress.
