from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

import repo_research_mcp.server as server_module
from repo_research_mcp.models import (
    DocumentMetadata,
    FetchedDocument,
    FetchResponse,
    FileEntry,
    ListFilesResponse,
    RepositoryOverview,
    RepositoryOverviewResponse,
    SearchResponse,
)
from repo_research_mcp.server import fetch, list_files, repository_overview, search


@pytest.fixture
def mock_svc(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    svc = MagicMock()
    monkeypatch.setattr(server_module, "_service", svc)
    return svc


def _http_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://api.github.com/test")
    response = httpx.Response(status_code=status, request=request)
    return httpx.HTTPStatusError(f"HTTP {status}", request=request, response=response)


def _search_response() -> SearchResponse:
    return SearchResponse(results=[])


def _fetch_response() -> FetchResponse:
    return FetchResponse(
        document=FetchedDocument(
            id="owner/repo::main::README.md",
            title="README.md",
            url="https://github.com/owner/repo/blob/main/README.md",  # type: ignore[arg-type]
            text="# Hello",
            metadata=DocumentMetadata(repository="owner/repo", path="README.md"),
        )
    )


def _overview_response() -> RepositoryOverviewResponse:
    return RepositoryOverviewResponse(
        overview=RepositoryOverview(
            repository="owner/repo",
            description=None,
            default_branch="main",
            url="https://github.com/owner/repo",  # type: ignore[arg-type]
            stars=0,
            forks=0,
            language=None,
            topics=[],
            file_count=1,
            file_tree=["README.md"],
            key_files=["README.md"],
            readme_excerpt="# Hello",
            tree_truncated=False,
        )
    )


def _list_files_response() -> ListFilesResponse:
    return ListFilesResponse(
        repository="owner/repo",
        path="",
        ref="main",
        entries=[
            FileEntry(
                name="README.md",
                path="README.md",
                type="file",
                sha="abc",
                size=100,
                url="https://github.com/owner/repo/blob/main/README.md",  # type: ignore[arg-type]
            )
        ],
    )


# --- search ---


@pytest.mark.asyncio
async def test_search_success(mock_svc: MagicMock) -> None:
    mock_svc.search = AsyncMock(return_value=_search_response())
    result = await search(query="hello", repository="owner/repo")
    assert "results" in result
    mock_svc.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_permission_denied(mock_svc: MagicMock) -> None:
    mock_svc.search = AsyncMock(side_effect=PermissionError("repo not allowed"))
    result = await search(query="x", repository="evil/repo")
    assert result["error"] == "permission_denied"
    assert "not allowed" in result["detail"]


@pytest.mark.asyncio
async def test_search_invalid_request(mock_svc: MagicMock) -> None:
    mock_svc.search = AsyncMock(side_effect=ValueError("bad input"))
    result = await search(query="x", repository="owner/repo")
    assert result["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_search_upstream_error(mock_svc: MagicMock) -> None:
    mock_svc.search = AsyncMock(side_effect=_http_error(403))
    result = await search(query="x", repository="owner/repo")
    assert result["error"] == "upstream_error"
    assert "403" in result["detail"]


@pytest.mark.asyncio
async def test_search_internal_error(mock_svc: MagicMock) -> None:
    mock_svc.search = AsyncMock(side_effect=RuntimeError("boom"))
    result = await search(query="x", repository="owner/repo")
    assert result["error"] == "internal_error"


# --- fetch ---


@pytest.mark.asyncio
async def test_fetch_success(mock_svc: MagicMock) -> None:
    mock_svc.fetch = AsyncMock(return_value=_fetch_response())
    result = await fetch(id="owner/repo::main::README.md")
    assert "document" in result
    assert result["document"]["title"] == "README.md"


@pytest.mark.asyncio
async def test_fetch_permission_denied(mock_svc: MagicMock) -> None:
    mock_svc.fetch = AsyncMock(side_effect=PermissionError("repo not allowed"))
    result = await fetch(id="evil/repo::main::file.py")
    assert result["error"] == "permission_denied"


@pytest.mark.asyncio
async def test_fetch_invalid_id(mock_svc: MagicMock) -> None:
    mock_svc.fetch = AsyncMock(side_effect=ValueError("invalid document id"))
    result = await fetch(id="badid")
    assert result["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_fetch_upstream_error(mock_svc: MagicMock) -> None:
    mock_svc.fetch = AsyncMock(side_effect=_http_error(404))
    result = await fetch(id="owner/repo::main::missing.py")
    assert result["error"] == "upstream_error"
    assert "404" in result["detail"]


# --- repository_overview ---


@pytest.mark.asyncio
async def test_overview_success(mock_svc: MagicMock) -> None:
    mock_svc.repository_overview = AsyncMock(return_value=_overview_response())
    result = await repository_overview(repository="owner/repo")
    assert "overview" in result
    assert result["overview"]["repository"] == "owner/repo"


@pytest.mark.asyncio
async def test_overview_permission_denied(mock_svc: MagicMock) -> None:
    mock_svc.repository_overview = AsyncMock(side_effect=PermissionError("not allowed"))
    result = await repository_overview(repository="evil/repo")
    assert result["error"] == "permission_denied"


@pytest.mark.asyncio
async def test_overview_upstream_error(mock_svc: MagicMock) -> None:
    mock_svc.repository_overview = AsyncMock(side_effect=_http_error(500))
    result = await repository_overview(repository="owner/repo")
    assert result["error"] == "upstream_error"
    assert "500" in result["detail"]


# --- list_files ---


@pytest.mark.asyncio
async def test_list_files_success(mock_svc: MagicMock) -> None:
    mock_svc.list_files = AsyncMock(return_value=_list_files_response())
    result = await list_files(repository="owner/repo")
    assert "entries" in result
    assert result["entries"][0]["name"] == "README.md"
    assert result["entries"][0]["type"] == "file"


@pytest.mark.asyncio
async def test_list_files_with_path(mock_svc: MagicMock) -> None:
    mock_svc.list_files = AsyncMock(return_value=_list_files_response())
    await list_files(repository="owner/repo", path="src", ref="develop")
    mock_svc.list_files.assert_awaited_once_with(
        repository="owner/repo", path="src", ref="develop"
    )


@pytest.mark.asyncio
async def test_list_files_permission_denied(mock_svc: MagicMock) -> None:
    mock_svc.list_files = AsyncMock(side_effect=PermissionError("not allowed"))
    result = await list_files(repository="evil/repo")
    assert result["error"] == "permission_denied"


@pytest.mark.asyncio
async def test_list_files_path_is_file(mock_svc: MagicMock) -> None:
    mock_svc.list_files = AsyncMock(side_effect=ValueError("path is a file"))
    result = await list_files(repository="owner/repo", path="README.md")
    assert result["error"] == "invalid_request"
    assert "file" in result["detail"]


@pytest.mark.asyncio
async def test_list_files_upstream_error(mock_svc: MagicMock) -> None:
    mock_svc.list_files = AsyncMock(side_effect=_http_error(404))
    result = await list_files(repository="owner/repo", path="missing/dir")
    assert result["error"] == "upstream_error"
