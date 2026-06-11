# Roadmap

This roadmap keeps `repo-research-mcp` focused on read-only repository research.

The project should evolve in small, reviewable phases. Each phase must preserve the boundaries defined in `docs/ADR-0001-purpose-and-scope.md`, `docs/ADR-0002-search-fetch-contract.md`, `AGENTS.md`, `CLAUDE.md`, and `docs/SECURITY.md`.

## Phase 0: Project foundation

Goal: define scope and make the repository safe for future agents.

Deliverables:

- README with purpose and constraints.
- Python project configuration.
- ADR-0001: purpose and scope.
- ADR-0002: search/fetch contract.
- AGENTS.md.
- CLAUDE.md.
- Security model.
- Minimal typed models.
- Minimal allowlist helper.
- Minimal stable document ID helper.

Exit criteria:

- Project scope is explicit.
- Forbidden operational actions are documented.
- Future agents have clear instructions.

## Phase 1: Local MVP

Goal: provide a small local implementation of the search/fetch contract without external indexing.

Deliverables:

- `search` tool skeleton.
- `fetch` tool skeleton.
- In-memory or simple file-backed provider for tests.
- Unit tests for allowlist behavior.
- Unit tests for document ID round-trips.
- Unit tests for search and fetch response shapes.
- Bounded result limits.

Exit criteria:

- Tests pass locally.
- The service can return deterministic search/fetch responses from a controlled provider.

## Phase 2: GitHub read-only provider

Goal: connect the service to GitHub read-only APIs while keeping a narrow research surface.

Deliverables:

- GitHub client abstraction.
- Repository tree discovery.
- File content fetch.
- Code/document search.
- Canonical GitHub URLs.
- Optional blob sha metadata.
- Rate-limit-aware error handling.
- Private repo handling documented before implementation.

Exit criteria:

- Allowed repositories can be searched and fetched.
- Disallowed repositories are blocked.
- No write GitHub API is exposed.

## Phase 3: MCP server integration

Goal: expose the local service through a real MCP server interface.

Deliverables:

- MCP server entrypoint.
- `search` tool.
- `fetch` tool.
- Environment-based configuration.
- Bounded outputs.
- Safe error responses.
- Dockerfile.
- CI workflow.

Exit criteria:

- MCP tools are callable locally.
- CI validates lint, typing, and tests.

## Phase 4: central-mcp-gateway integration

Goal: register `repo-research-mcp` as a research-only upstream behind `central-mcp-gateway`.

Deliverables:

- Gateway catalog proposal.
- Read-only tool annotations.
- Deployment documentation.
- Smoke test instructions.
- Security review against gateway policy.

Exit criteria:

- Gateway can discover `search` and `fetch`.
- Gateway classifies the tools as read-only.
- No write, destructive, external-publication, or paid-operation tool is exposed.

## Phase 5: Deep Research compatibility

Goal: make the service useful as a repository source for Deep Research-style workflows.

Deliverables:

- Better ranking.
- Better snippets.
- Documentation-aware search.
- File type filtering.
- Repository overview result.
- Architecture summary helpers if they remain read-only and bounded.

Exit criteria:

- Search results are citation-friendly.
- Fetch results are stable and bounded.
- Repository research produces useful context without operational permissions.

## Non-goals

The roadmap does not include GitHub mutations, deploy orchestration, shell execution, sandbox execution, social publishing, or paid provider calls.

Those capabilities belong in other services and should not be added here without a new ADR.
