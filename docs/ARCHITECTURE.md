# Architecture

`repo-research-mcp` is a narrow read-only repository research service.

It is designed to sit behind `central-mcp-gateway` and expose only a small document retrieval contract to research clients.

## High-level flow

A research client calls `central-mcp-gateway`. The gateway routes approved read-only calls to `repo-research-mcp`. The service validates the repository allowlist, reads from a repository provider, and returns bounded search or fetch results with canonical source URLs.

## Public MCP surface

The initial public surface is intentionally small:

- `search`: discover relevant repository documents.
- `fetch`: retrieve one document by an ID returned by `search`.

The service must not expose operational GitHub tools.

## Internal components

### Settings

Loads runtime configuration such as allowed repositories, default branch, maximum result count, maximum fetch size, and optional GitHub token.

### RepositoryAllowlist

Normalizes and validates repository names.

Every repository access must pass through this component.

### Document ID helper

Creates and parses stable document IDs used for search/fetch round-trips.

IDs are treated as untrusted input when received by `fetch`.

### Models

Defines typed shapes for repository refs, document metadata, search results, fetched documents, and tool responses.

Tool boundaries should prefer these models over ad-hoc dictionaries.

### Research service

Coordinates allowlist validation, search result creation, fetch result creation, metadata, and canonical URLs.

The current bootstrap contains a placeholder. The full implementation should be added in a later phase.

### Repository provider

Abstracts the read-only source of repository documents.

Initial providers may be in-memory or file-backed for tests. A GitHub read-only provider should be added later.

## Trust boundaries

Repository content, user queries, and document IDs are untrusted input.

GitHub tokens are secrets.

`central-mcp-gateway` policy is an additional safety layer, not a replacement for service-level checks.

## Read-only enforcement

The service must not implement repository mutations.

Any future tool must be read-only, bounded, and justified by repository research use cases. If a future feature expands scope, it requires a new ADR before implementation.

## Output strategy

Search should return compact snippets with stable IDs and canonical URLs.

Fetch should return bounded full document text with metadata. Large files should be truncated safely or rejected with a clear error.

## Deployment shape

The expected deployment path is:

1. Run `repo-research-mcp` as a small Python service.
2. Configure allowed repositories through environment variables.
3. Use a read-only GitHub token when private repositories are required.
4. Register the service as an upstream in `central-mcp-gateway`.
5. Approve only read-only `search` and `fetch` catalog entries.

## Non-goal architecture

This service is not a replacement for `github-unified-mcp`.

Operational actions such as issue mutation, PR creation, workflow dispatch, branch deletion, deploys, shell execution, sandbox execution, and social publishing belong outside this service.
