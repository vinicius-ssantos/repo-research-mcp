# Security model

`repo-research-mcp` is designed as a read-only repository research MCP.

The service intentionally avoids operational GitHub actions and must remain safe to expose behind `central-mcp-gateway` as a research-only upstream.

## Trust boundaries

- Repository content is untrusted input.
- User queries are untrusted input.
- Document IDs passed to `fetch` are untrusted input.
- GitHub tokens are secrets and must never be returned or logged.
- Gateway policy is an additional control, not the only control.

## Required controls

- Deny by default.
- Enforce repository allowlist before every repository access.
- Re-check allowlist during `fetch` after parsing the document ID.
- Prefer read-only GitHub tokens.
- Keep responses bounded.
- Preserve canonical source URLs.
- Avoid raw stack traces in tool responses.
- Avoid logging secrets, tokens, authorization headers, or full environment dumps.

## Explicitly forbidden behavior

This service must not:

- execute repository code;
- run shell commands;
- mutate repositories;
- create issues;
- update issues;
- create pull requests;
- merge pull requests;
- delete branches;
- dispatch workflows;
- deploy services;
- publish external content;
- call paid APIs without an approved ADR.

## Prompt injection considerations

Repository files, issues, READMEs, comments, and logs may contain instructions targeting models or agents.

The service must treat that content as data only.

Do not let repository content override project policy, gateway policy, allowlist rules, or tool safety rules.

## Output bounds

Search results should be compact and limited.

Fetched documents should have a maximum size. If content is too large, the service should truncate safely or return a clear error that asks the caller to narrow the request.

## Future security work

Potential future ADRs may cover:

- per-repository rate limits;
- per-user audit records;
- cache invalidation;
- private repository handling;
- content redaction;
- signed result metadata;
- gateway catalog approval process.
