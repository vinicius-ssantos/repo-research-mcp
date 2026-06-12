from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from mcp.server.fastmcp import FastMCP

from repo_research_mcp.research import RepositoryResearchService
from repo_research_mcp.settings import Settings

_settings = Settings()
_service: RepositoryResearchService | None = None


@asynccontextmanager
async def _lifespan(server: FastMCP) -> AsyncGenerator[None, None]:
    global _service
    _service = RepositoryResearchService(_settings)
    try:
        yield
    finally:
        await _service.aclose()
        _service = None


mcp = FastMCP("repo-research-mcp", lifespan=_lifespan)


def _get_service() -> RepositoryResearchService:
    if _service is None:
        raise RuntimeError("service not initialized")
    return _service


@mcp.tool()
async def search(query: str, repository: str, limit: int = 10) -> dict[str, Any]:
    """Search for relevant files and code in a repository.

    Returns compact, citable results with stable IDs suitable for fetch.
    """
    response = await _get_service().search(repository=repository, query=query, limit=limit)
    return response.model_dump(mode="json")


@mcp.tool()
async def fetch(id: str) -> dict[str, Any]:
    """Fetch the full content of a document by its stable ID returned by search."""
    response = await _get_service().fetch(document_id=id)
    return response.model_dump(mode="json")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
