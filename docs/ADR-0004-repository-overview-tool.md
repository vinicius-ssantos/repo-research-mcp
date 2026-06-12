# ADR-0004: repository_overview tool

## Status

Accepted

## Context

Research clients performing Deep Research-style analysis need a fast starting point for an unfamiliar repository: what the project does, what its structure looks like, and where the key documents are.

Currently, a client must call `search` with several queries to discover this shape. A dedicated overview tool reduces round-trips and provides a richer initial context in one response.

## Decision

Add a third read-only MCP tool: `repository_overview(repository)`.

The tool fetches and returns:

- Repository metadata (description, stars, forks, primary language, topics).
- A bounded file tree of all blobs in the default ref.
- A list of identified key files (README, CHANGELOG, architecture docs, config files).
- A truncated README excerpt for quick context.
- A flag indicating whether the file tree was truncated by GitHub or the service limit.

## Read-only guarantee

The tool uses three GitHub read-only endpoints:
- `GET /repos/{owner}/{repo}` — metadata only, no writes.
- `GET /repos/{owner}/{repo}/git/trees/{ref}?recursive=1` — tree only, no writes.
- `GET /repos/{owner}/{repo}/readme` — content only, no writes.

No mutation of the repository is possible through this tool.

## Allowlist enforcement

The allowlist is checked before any GitHub API call, exactly as in `search` and `fetch`.

## Output bounds

- File tree: bounded to 300 paths. If GitHub returns a truncated tree or the service limit is reached, `tree_truncated` is set to `true`.
- README excerpt: bounded to 2 000 bytes. Larger READMEs are truncated with a notice.

## Scope

This tool is read-only repository research. It does not:

- mutate the repository;
- create issues or pull requests;
- execute repository code;
- call paid APIs.

## Consequences

Clients can orient themselves in one call instead of several search queries.

The `repository_overview` tool is approved for gateway exposure with `read_only: true` annotation alongside `search` and `fetch`.

The ADR-0003 gateway registration doc should be updated to include this tool.
