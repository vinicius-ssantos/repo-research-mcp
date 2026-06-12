from __future__ import annotations

from repo_research_mcp.allowlist import RepositoryAllowlist
from repo_research_mcp.github_provider import GitHubProvider, RepositoryProvider
from repo_research_mcp.ids import make_document_id, parse_document_id
from repo_research_mcp.models import (
    DocumentMetadata,
    FetchedDocument,
    FetchResponse,
    SearchResponse,
    SearchResult,
)
from repo_research_mcp.settings import Settings

_BLOB_URL = "https://github.com/{owner}/{repo}/blob/{ref}/{path}"


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
            results.append(
                SearchResult(
                    id=doc_id,
                    title=match.path,
                    url=url,  # type: ignore[arg-type]
                    text=match.snippet or match.path,
                    metadata=DocumentMetadata(
                        repository=repo_ref.full_name,
                        path=match.path,
                        ref=ref,
                        sha=match.sha,
                    ),
                )
            )
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
