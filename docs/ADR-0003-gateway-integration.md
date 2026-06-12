# ADR-0003: central-mcp-gateway integration

## Status

Accepted

## Context

`repo-research-mcp` is designed to run behind `central-mcp-gateway` as a research-only upstream.

The gateway controls which tools are exposed to external callers. This ADR documents how to register, annotate, and verify the service within the gateway.

## Decision

Register `repo-research-mcp` as a named upstream in `central-mcp-gateway` with read-only tool annotations.

Only `search` and `fetch` are approved for gateway exposure. No operational tool from another MCP should be proxied through this service.

## Registration

Add the following upstream entry to the gateway catalog:

```yaml
upstreams:
  - name: repo-research-mcp
    transport: stdio
    command: repo-research-mcp
    env:
      REPO_RESEARCH_ALLOWED_REPOSITORIES: '["owner/repo"]'
      REPO_RESEARCH_GITHUB_TOKEN: "${GITHUB_TOKEN}"
    tools:
      - name: search
        read_only: true
        description: Search for relevant files and code in an allowed repository.
      - name: fetch
        read_only: true
        description: Fetch the full content of a document by its stable ID.
      - name: repository_overview
        read_only: true
        description: Return a structured overview of a repository for research orientation.
```

## Tool annotations

Both tools must be annotated `read_only: true` in the gateway catalog.

The gateway should not expose any tool that is not on the approved list above.

## Allowed repositories

Configure `REPO_RESEARCH_ALLOWED_REPOSITORIES` with a JSON array of `owner/repo` strings.

The service enforces the allowlist independently, but the gateway should also restrict which repositories callers can request when possible.

## Security review checklist

Before approving the catalog entry:

- [ ] Confirm `search` makes no write GitHub API calls.
- [ ] Confirm `fetch` makes no write GitHub API calls.
- [ ] Confirm no tool exposes GitHub tokens in its response.
- [ ] Confirm no tool accepts a repository outside the configured allowlist.
- [ ] Confirm error responses do not include raw stack traces.
- [ ] Confirm the service does not execute repository code.
- [ ] Confirm bounded output limits are active (`REPO_RESEARCH_MAX_FETCH_BYTES`).

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `REPO_RESEARCH_ALLOWED_REPOSITORIES` | Yes | `[]` | JSON array of allowed `owner/repo` strings |
| `REPO_RESEARCH_GITHUB_TOKEN` | Recommended | None | Read-only GitHub token |
| `REPO_RESEARCH_DEFAULT_REF` | No | `main` | Default branch or ref |
| `REPO_RESEARCH_MAX_SEARCH_RESULTS` | No | `10` | Maximum results per search (1–50) |
| `REPO_RESEARCH_MAX_FETCH_BYTES` | No | `100000` | Maximum bytes per fetch |

## Smoke test

After registration, verify the integration:

```bash
# search should return results or an empty list
mcp call search '{"query": "README", "repository": "owner/repo"}'

# fetch should return document content
mcp call fetch '{"id": "<id from search result>"}'

# disallowed repo should return permission_denied
mcp call search '{"query": "test", "repository": "disallowed/repo"}'
```

## Non-goal

This service must not be used as a proxy for `github-unified-mcp` operational tools.

Requests for write, mutation, or operational GitHub actions must be routed to a different upstream.

## Consequences

Research clients connected through `central-mcp-gateway` gain read-only repository research capability without receiving operational GitHub permissions.

The narrow tool surface reduces the attack area and simplifies gateway policy audits.
