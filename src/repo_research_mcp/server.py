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


def _upstream_error(exc: httpx.HTTPStatusError) -> dict[str, Any]:
    return {"error": "upstream_error", "detail": f"GitHub API returned {exc.response.status_code}"}


@mcp.tool()
async def search(
    query: str,
    repository: str,
    limit: int = 10,
    file_extension: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    """Search for relevant files and code in a repository.

    Results are ranked with documentation files first.
    Optionally filter by file extension (e.g. "py", ".ts") or language (e.g. "Python").
    """
    try:
        response = await _get_service().search(
            repository=repository,
            query=query,
            limit=limit,
            file_extension=file_extension,
            language=language,
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
        return _upstream_error(exc)
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
        return _upstream_error(exc)
    except Exception:
        logger.exception("unexpected error during fetch")
        return {"error": "internal_error", "detail": "An unexpected error occurred."}


@mcp.tool()
async def repository_overview(repository: str) -> dict[str, Any]:
    """Return a structured overview of a repository for research orientation.

    Includes metadata (description, stars, language), file tree, key files,
    and a README excerpt. Useful as a first call before searching.
    """
    try:
        response = await _get_service().repository_overview(repository=repository)
        result: dict[str, Any] = response.model_dump(mode="json")
        return result
    except PermissionError as exc:
        logger.warning("repository_overview permission denied: %s", exc)
        return {"error": "permission_denied", "detail": str(exc)}
    except ValueError as exc:
        return {"error": "invalid_request", "detail": str(exc)}
    except httpx.HTTPStatusError as exc:
        logger.error("GitHub API error during repository_overview: %s", exc.response.status_code)
        return _upstream_error(exc)
    except Exception:
        logger.exception("unexpected error during repository_overview")
        return {"error": "internal_error", "detail": "An unexpected error occurred."}


@mcp.tool()
async def list_files(
    repository: str,
    path: str = "",
    ref: str | None = None,
) -> dict[str, Any]:
    """List files and directories at a path in a repository.

    Returns immediate children only (not recursive). Use path="" for the root.
    Use fetch to retrieve the content of a specific file.
    """
    try:
        response = await _get_service().list_files(
            repository=repository,
            path=path,
            ref=ref,
        )
        result: dict[str, Any] = response.model_dump(mode="json")
        return result
    except PermissionError as exc:
        logger.warning("list_files permission denied: %s", exc)
        return {"error": "permission_denied", "detail": str(exc)}
    except ValueError as exc:
        return {"error": "invalid_request", "detail": str(exc)}
    except httpx.HTTPStatusError as exc:
        logger.error("GitHub API error during list_files: %s", exc.response.status_code)
        return _upstream_error(exc)
    except Exception:
        logger.exception("unexpected error during list_files")
        return {"error": "internal_error", "detail": "An unexpected error occurred."}


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    mcp.run()


if __name__ == "__main__":
    main()
