# ADR-0005: list_files tool

## Status

Accepted

## Context

`repository_overview` returns a bounded flat file tree (max 300 entries) which is useful for orientation but insufficient for navigating large repositories or drilling into specific directories.

Research clients need to browse the structure of a specific path — for example, listing what is inside `src/`, `docs/`, or `.github/workflows/` — without fetching every file's content.

A `list_files` tool closes this gap while remaining read-only and allowlist-bounded.

## Decision

Add a fourth read-only MCP tool: `list_files(repository, path, ref)`.

The tool returns the immediate children of a path (files and sub-directories) using the GitHub contents API. It does not recurse — one call = one directory level.

## Read-only guarantee

Uses only `GET /repos/{owner}/{repo}/contents/{path}?ref={ref}`, which is a read-only GitHub endpoint.

## Allowlist enforcement

The allowlist is checked before any API call, as in all other tools.

## Output

Each entry includes:
- `name`: filename or directory name.
- `path`: repository-relative path.
- `type`: `"file"` or `"dir"`.
- `sha`: blob or tree SHA.
- `size`: bytes for files; `None` for directories.
- `url`: canonical GitHub URL (blob for files, tree for directories).

If `path` points to a file rather than a directory the tool returns an error asking the caller to use `fetch` instead.

## Scope

This tool is read-only repository navigation. It does not:

- fetch file content (use `fetch` for that);
- mutate the repository;
- execute code.

## Consequences

Research clients can progressively explore repository structure without reading file content.

The `list_files` tool is approved for gateway exposure with `read_only: true` annotation.

The ADR-0003 gateway registration doc should be updated to include this tool.
