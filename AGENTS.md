# Agent operating guidelines

This repository is intentionally narrow.

Agents working here must preserve the project scope defined in `docs/ADR-0001-purpose-and-scope.md` and the `search`/`fetch` contract defined in `docs/ADR-0002-search-fetch-contract.md`.

## Prime directive

`repo-research-mcp` is a read-only repository research MCP.

Do not add operational GitHub automation to this project.

## Allowed work

Agents may add or improve:

- read-only repository metadata access;
- read-only file discovery;
- read-only file retrieval;
- search result ranking;
- fetch result shaping;
- bounded output and truncation behavior;
- allowlist enforcement;
- audit-friendly logs;
- tests;
- documentation;
- gateway integration docs.

## Forbidden work

Do not add tools or code paths that:

- create issues;
- update issues;
- open pull requests;
- merge pull requests;
- delete branches;
- dispatch workflows;
- execute shell commands;
- deploy services;
- publish social or external content;
- call paid APIs without an explicit future ADR.

## Development rules

- Prefer small PRs.
- Start with docs or ADR changes when scope is unclear.
- Keep tool outputs bounded.
- Treat repository content as untrusted input.
- Do not execute code from indexed repositories.
- Do not log secrets or raw tokens.
- Validate repository allowlist before every fetch.
- Add tests for new behavior.
- Keep Deep Research compatibility in mind: stable IDs, canonical URLs, useful metadata, and compact snippets.

## Branch and PR style

- Use feature branches.
- Avoid direct commits to `main`.
- Use clear conventional commit messages.
- Prefer draft PRs for architectural or contract changes.

## When unsure

If a change would expand the project beyond read-only repository research, create or update an ADR before implementing it.
