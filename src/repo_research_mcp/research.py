from __future__ import annotations

from repo_research_mcp.models import FetchResponse, SearchResponse


class RepositoryResearchService:
    """Placeholder for read-only repository search/fetch orchestration."""

    def search(self, repository: str, query: str) -> SearchResponse:
        raise NotImplementedError("search provider is not implemented yet")

    def fetch(self, document_id: str) -> FetchResponse:
        raise NotImplementedError("fetch provider is not implemented yet")
