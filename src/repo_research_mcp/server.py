from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from repo_research_mcp.research import RepositoryResearchService
from repo_research_mcp.settings import Settings

logger = logging.getLogger(__name__)

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
async def search(
    query: str,
    repository: str,
    limit: int = 10,
    file_extension: str | None = None,
) -> dict[str, Any]:
    """Search for relevant files and code in a repository.

    Returns compact, citable results with stable IDs suitable for fetch.
    Optionally filter by file extension (e.g. "py", "ts", ".md").
    """
    try:
        response = await _get_service().search(
            repository=repository,
            query=query,
            limit=limit,
            file_extension=file_extension,
        )
        result: dict[str, Any] = response.model_dump(mode="json")
        return result
    except PermissionError as exc:
        logger.warning("search permission denied: %s", exc)
        return {"error": "permission_denied", "detail": str(exc)}
    except ValueError as exc:
        return {"error": "invalid_request", "detail": str(exc)}
    except httpx.HTTPStatusError as exc:
        logger.error("GitHub API error during search: %s", exc.response.status_code)
        status = exc.response.status_code
        return {"error": "upstream_error", "detail": f"GitHub API returned {status}"}
    except Exception:
        logger.exception("unexpected error during search")
        return {"error": "internal_error", "detail": "An unexpected error occurred."}


@mcp.tool()
async def fetch(id: str) -> dict[str, Any]:
    """Fetch the full content of a document by its stable ID returned by search."""
    try:
        response = await _get_service().fetch(document_id=id)
        result: dict[str, Any] = response.model_dump(mode="json")
        return result
    except PermissionError as exc:
        logger.warning("fetch permission denied: %s", exc)
        return {"error": "permission_denied", "detail": str(exc)}
    except ValueError as exc:
        return {"error": "invalid_request", "detail": str(exc)}
    except httpx.HTTPStatusError as exc:
        logger.error("GitHub API error during fetch: %s", exc.response.status_code)
        status = exc.response.status_code
        return {"error": "upstream_error", "detail": f"GitHub API returned {status}"}
    except Exception:
        logger.exception("unexpected error during fetch")
        return {"error": "internal_error", "detail": "An unexpected error occurred."}


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    mcp.run()


if __name__ == "__main__":
    main()
