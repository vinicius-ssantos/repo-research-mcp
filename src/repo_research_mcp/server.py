from __future__ import annotations

import logging
import os
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from repo_research_mcp.logging_config import configure_logging, new_request_id
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


def _configure_streamable_http_transport() -> None:
    from mcp.server.transport_security import TransportSecuritySettings

    mcp.settings.host = os.getenv("MCP_HOST", "0.0.0.0")
    mcp.settings.port = int(os.getenv("MCP_PORT", "8081"))
    mcp.settings.json_response = True
    mcp.settings.stateless_http = True
    allowed = os.getenv("FASTMCP_ALLOWED_HOSTS", "")
    if allowed:
        mcp.settings.transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[h.strip() for h in allowed.split(",") if h.strip()],
        )
    else:
        mcp.settings.transport_security = None


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
    page: int = 1,
) -> dict[str, Any]:
    """Search for relevant files and code in a repository.

    Results are ranked with documentation files first.
    Optionally filter by file extension (e.g. "py", ".ts") or language (e.g. "Python").
    Use page to paginate through results (default 1).
    """
    new_request_id()
    t0 = time.monotonic()
    try:
        response = await _get_service().search(
            repository=repository,
            query=query,
            limit=limit,
            file_extension=file_extension,
            language=language,
            page=page,
        )
        duration = int((time.monotonic() - t0) * 1000)
        logger.info(
            "search ok",
            extra={
                "tool": "search",
                "repository": repository,
                "duration_ms": duration,
                "result_count": len(response.results),
            },
        )
        result: dict[str, Any] = response.model_dump(mode="json")
        return result
    except PermissionError as exc:
        logger.warning(
            "search denied",
            extra={"tool": "search", "repository": repository, "error_type": "permission_denied"},
        )
        return {"error": "permission_denied", "detail": str(exc)}
    except ValueError as exc:
        logger.warning(
            "search invalid",
            extra={"tool": "search", "repository": repository, "error_type": "invalid_request"},
        )
        return {"error": "invalid_request", "detail": str(exc)}
    except httpx.HTTPStatusError as exc:
        logger.error(
            "search upstream error",
            extra={
                "tool": "search",
                "repository": repository,
                "error_type": "upstream_error",
                "duration_ms": int((time.monotonic() - t0) * 1000),
            },
        )
        return _upstream_error(exc)
    except Exception:
        logger.exception(
            "search internal error",
            extra={"tool": "search", "repository": repository, "error_type": "internal_error"},
        )
        return {"error": "internal_error", "detail": "An unexpected error occurred."}


@mcp.tool()
async def fetch(id: str) -> dict[str, Any]:
    """Fetch the full content of a document by its stable ID returned by search."""
    new_request_id()
    t0 = time.monotonic()
    try:
        response = await _get_service().fetch(document_id=id)
        duration = int((time.monotonic() - t0) * 1000)
        logger.info(
            "fetch ok",
            extra={"tool": "fetch", "duration_ms": duration},
        )
        result: dict[str, Any] = response.model_dump(mode="json")
        return result
    except PermissionError as exc:
        logger.warning(
            "fetch denied",
            extra={"tool": "fetch", "error_type": "permission_denied"},
        )
        return {"error": "permission_denied", "detail": str(exc)}
    except ValueError as exc:
        logger.warning(
            "fetch invalid",
            extra={"tool": "fetch", "error_type": "invalid_request"},
        )
        return {"error": "invalid_request", "detail": str(exc)}
    except httpx.HTTPStatusError as exc:
        logger.error(
            "fetch upstream error",
            extra={
                "tool": "fetch",
                "error_type": "upstream_error",
                "duration_ms": int((time.monotonic() - t0) * 1000),
            },
        )
        return _upstream_error(exc)
    except Exception:
        logger.exception(
            "fetch internal error",
            extra={"tool": "fetch", "error_type": "internal_error"},
        )
        return {"error": "internal_error", "detail": "An unexpected error occurred."}


@mcp.tool()
async def repository_overview(repository: str) -> dict[str, Any]:
    """Return a structured overview of a repository for research orientation.

    Includes metadata (description, stars, language), file tree, key files,
    and a README excerpt. Useful as a first call before searching.
    """
    new_request_id()
    t0 = time.monotonic()
    try:
        response = await _get_service().repository_overview(repository=repository)
        duration = int((time.monotonic() - t0) * 1000)
        logger.info(
            "repository_overview ok",
            extra={
                "tool": "repository_overview",
                "repository": repository,
                "duration_ms": duration,
            },
        )
        result: dict[str, Any] = response.model_dump(mode="json")
        return result
    except PermissionError as exc:
        logger.warning(
            "repository_overview denied",
            extra={
                "tool": "repository_overview",
                "repository": repository,
                "error_type": "permission_denied",
            },
        )
        return {"error": "permission_denied", "detail": str(exc)}
    except ValueError as exc:
        logger.warning(
            "repository_overview invalid",
            extra={
                "tool": "repository_overview",
                "repository": repository,
                "error_type": "invalid_request",
            },
        )
        return {"error": "invalid_request", "detail": str(exc)}
    except httpx.HTTPStatusError as exc:
        logger.error(
            "repository_overview upstream error",
            extra={
                "tool": "repository_overview",
                "repository": repository,
                "error_type": "upstream_error",
                "duration_ms": int((time.monotonic() - t0) * 1000),
            },
        )
        return _upstream_error(exc)
    except Exception:
        logger.exception(
            "repository_overview internal error",
            extra={
                "tool": "repository_overview",
                "repository": repository,
                "error_type": "internal_error",
            },
        )
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
    new_request_id()
    t0 = time.monotonic()
    try:
        response = await _get_service().list_files(
            repository=repository,
            path=path,
            ref=ref,
        )
        duration = int((time.monotonic() - t0) * 1000)
        logger.info(
            "list_files ok",
            extra={
                "tool": "list_files",
                "repository": repository,
                "duration_ms": duration,
                "result_count": len(response.entries),
            },
        )
        result: dict[str, Any] = response.model_dump(mode="json")
        return result
    except PermissionError as exc:
        logger.warning(
            "list_files denied",
            extra={
                "tool": "list_files",
                "repository": repository,
                "error_type": "permission_denied",
            },
        )
        return {"error": "permission_denied", "detail": str(exc)}
    except ValueError as exc:
        logger.warning(
            "list_files invalid",
            extra={"tool": "list_files", "repository": repository, "error_type": "invalid_request"},
        )
        return {"error": "invalid_request", "detail": str(exc)}
    except httpx.HTTPStatusError as exc:
        logger.error(
            "list_files upstream error",
            extra={
                "tool": "list_files",
                "repository": repository,
                "error_type": "upstream_error",
                "duration_ms": int((time.monotonic() - t0) * 1000),
            },
        )
        return _upstream_error(exc)
    except Exception:
        logger.exception(
            "list_files internal error",
            extra={"tool": "list_files", "repository": repository, "error_type": "internal_error"},
        )
        return {"error": "internal_error", "detail": "An unexpected error occurred."}


def main() -> None:
    configure_logging(_settings.log_format)
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        _configure_streamable_http_transport()
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
