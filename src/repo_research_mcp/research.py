from __future__ import annotations

import asyncio

from repo_research_mcp.allowlist import RepositoryAllowlist
from repo_research_mcp.github_provider import GitHubProvider, RepositoryProvider
from repo_research_mcp.ids import make_document_id, parse_document_id
from repo_research_mcp.models import (
    DocumentMetadata,
    FetchedDocument,
    FetchResponse,
    RepositoryOverview,
    RepositoryOverviewResponse,
    SearchResponse,
    SearchResult,
)
from repo_research_mcp.settings import Settings

_BLOB_URL = "https://github.com/{owner}/{repo}/blob/{ref}/{path}"
_REPO_URL = "https://github.com/{owner}/{repo}"

_KEY_FILE_NAMES: frozenset[str] = frozenset({
    "readme.md", "readme.txt", "readme.rst", "readme",
    "changelog.md", "changelog.txt", "changelog.rst", "changelog",
    "contributing.md", "contributing.txt", "contributing",
    "license", "license.md", "license.txt",
    "security.md", "security.txt",
    "architecture.md",
    "roadmap.md",
    "agents.md",
    "claude.md",
    "makefile",
    "dockerfile",
    "docker-compose.yml", "docker-compose.yaml",
    "pyproject.toml",
    "setup.py", "setup.cfg",
    "package.json",
    "cargo.toml",
    "go.mod",
    "codeowners",
})

_DOC_STEM_NAMES: frozenset[str] = frozenset({
    "readme", "changelog", "contributing", "architecture",
    "security", "license", "roadmap", "agents", "claude",
    "codeowners",
})

_DOC_DIRS: frozenset[str] = frozenset({"docs", "doc", ".github"})


def _result_score(path: str) -> int:
    """Higher score = shown earlier in search results."""
    parts = path.lower().replace("\\", "/").split("/")
    name = parts[-1]
    stem = name.rsplit(".", 1)[0] if "." in name else name

    if stem in _DOC_STEM_NAMES:
        return 3
    if any(p in _DOC_DIRS for p in parts[:-1]):
        return 2
    if len(parts) == 1:
        return 1
    return 0


def _identify_key_files(tree: list[str]) -> list[str]:
    result: list[str] = []
    for path in tree:
        lower = path.lower()
        name = lower.split("/")[-1]
        if name in _KEY_FILE_NAMES or lower in _KEY_FILE_NAMES:
            result.append(path)
    return result


class RepositoryResearchService:
    """Read-only repository search and fetch orchestration."""

    def __init__(
        self,
        settings: Settings,
        provider: RepositoryProvider | None = None,
    ) -> None:
        self._settings = settings
        self._allowlist = RepositoryAllowlist(settings.allowed_repositories)
        self._provider = provider or GitHubProvider(token=settings.github_token)

    async def aclose(self) -> None:
        await self._provider.aclose()

    async def search(
        self,
        repository: str,
        query: str,
        limit: int | None = None,
        file_extension: str | None = None,
        language: str | None = None,
    ) -> SearchResponse:
        repo_ref = self._allowlist.require(repository)
        ref = self._settings.default_ref
        max_results = min(
            limit if limit is not None else self._settings.max_search_results,
            self._settings.max_search_results,
        )

        matches = await self._provider.search_code(
            owner=repo_ref.owner,
            repo=repo_ref.repo,
            query=query,
            limit=max_results,
            file_extension=file_extension,
            language=language,
        )

        results: list[SearchResult] = []
        for match in matches:
            doc_id = make_document_id(repo_ref.full_name, match.path, ref)
            url = _BLOB_URL.format(
                owner=repo_ref.owner,
                repo=repo_ref.repo,
                ref=ref,
                path=match.path,
            )
            snippet = match.snippet or f"[matched by filename: {match.path.split('/')[-1]}]"
            results.append(
                SearchResult(
                    id=doc_id,
                    title=match.path,
                    url=url,  # type: ignore[arg-type]
                    text=snippet,
                    metadata=DocumentMetadata(
                        repository=repo_ref.full_name,
                        path=match.path,
                        ref=ref,
                        sha=match.sha,
                    ),
                )
            )

        results.sort(key=lambda r: _result_score(r.metadata.path), reverse=True)
        return SearchResponse(results=results)

    async def fetch(self, document_id: str) -> FetchResponse:
        repository, ref, path = parse_document_id(document_id)
        repo_ref = self._allowlist.require(repository)

        content = await self._provider.fetch_file(
            owner=repo_ref.owner,
            repo=repo_ref.repo,
            path=path,
            ref=ref,
            max_bytes=self._settings.max_fetch_bytes,
        )

        url = _BLOB_URL.format(
            owner=repo_ref.owner,
            repo=repo_ref.repo,
            ref=ref,
            path=path,
        )

        text = content.text
        if content.truncated:
            text += (
                f"\n\n[truncated — file size {content.size} bytes"
                f" exceeds limit {self._settings.max_fetch_bytes}]"
            )

        return FetchResponse(
            document=FetchedDocument(
                id=document_id,
                title=path,
                url=url,  # type: ignore[arg-type]
                text=text,
                metadata=DocumentMetadata(
                    repository=repo_ref.full_name,
                    path=path,
                    ref=ref,
                    sha=content.sha,
                ),
            )
        )

    async def repository_overview(self, repository: str) -> RepositoryOverviewResponse:
        repo_ref = self._allowlist.require(repository)
        ref = self._settings.default_ref

        info, (tree, tree_truncated), readme = await asyncio.gather(
            self._provider.fetch_repository_info(repo_ref.owner, repo_ref.repo),
            self._provider.fetch_tree(repo_ref.owner, repo_ref.repo, ref),
            self._provider.fetch_readme(
                repo_ref.owner, repo_ref.repo, ref, max_bytes=2_000
            ),
        )

        url = _REPO_URL.format(owner=repo_ref.owner, repo=repo_ref.repo)

        return RepositoryOverviewResponse(
            overview=RepositoryOverview(
                repository=repo_ref.full_name,
                description=info.description,
                default_branch=info.default_branch,
                url=url,  # type: ignore[arg-type]
                stars=info.stars,
                forks=info.forks,
                language=info.language,
                topics=info.topics,
                file_count=len(tree),
                file_tree=tree,
                key_files=_identify_key_files(tree),
                readme_excerpt=readme,
                tree_truncated=tree_truncated,
            )
        )
