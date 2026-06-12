from __future__ import annotations

import pytest

from repo_research_mcp.github_provider import FileContent, FileMatch, RepositoryProvider
from repo_research_mcp.ids import make_document_id
from repo_research_mcp.research import RepositoryResearchService
from repo_research_mcp.settings import Settings


class InMemoryProvider(RepositoryProvider):
    """Simple in-memory provider for tests."""

    def __init__(self, files: dict[str, str]) -> None:
        self._files = files
        self.last_search_extension: str | None = None

    async def search_code(
        self,
        owner: str,
        repo: str,
        query: str,
        limit: int,
        file_extension: str | None = None,
    ) -> list[FileMatch]:
        self.last_search_extension = file_extension
        results: list[FileMatch] = []
        for path, content in self._files.items():
            if file_extension:
                ext = file_extension.lstrip(".")
                if not path.endswith(f".{ext}"):
                    continue
            if query.lower() in content.lower() or query.lower() in path.lower():
                results.append(
                    FileMatch(
                        path=path,
                        sha="deadbeef",
                        html_url=f"https://github.com/{owner}/{repo}/blob/main/{path}",
                        snippet=content[:200],
                    )
                )
        return results[:limit]

    async def fetch_file(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str,
        max_bytes: int,
    ) -> FileContent:
        if path not in self._files:
            raise FileNotFoundError(f"file not found: {path}")
        content = self._files[path]
        raw = content.encode()
        truncated = len(raw) > max_bytes
        return FileContent(
            path=path,
            sha="deadbeef",
            html_url=f"https://github.com/{owner}/{repo}/blob/{ref}/{path}",
            text=content[:max_bytes],
            size=len(raw),
            truncated=truncated,
        )


def _make_service(
    repos: list[str],
    files: dict[str, str],
    max_results: int = 10,
    max_fetch_bytes: int = 100_000,
) -> tuple[RepositoryResearchService, InMemoryProvider]:
    settings = Settings(
        allowed_repositories=repos,
        max_search_results=max_results,
        max_fetch_bytes=max_fetch_bytes,
    )
    provider = InMemoryProvider(files)
    return RepositoryResearchService(settings, provider=provider), provider


# --- search ---


@pytest.mark.asyncio
async def test_search_returns_matching_results() -> None:
    svc, _ = _make_service(
        repos=["owner/repo"],
        files={"src/main.py": "def hello_world(): pass", "README.md": "# hello"},
    )
    response = await svc.search("owner/repo", "hello")
    assert len(response.results) == 2
    paths = {r.metadata.path for r in response.results}
    assert "src/main.py" in paths
    assert "README.md" in paths


@pytest.mark.asyncio
async def test_search_result_has_stable_id() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={"file.py": "content"})
    response = await svc.search("owner/repo", "content")
    assert len(response.results) == 1
    result = response.results[0]
    assert result.id == make_document_id("owner/repo", "file.py", "main")


@pytest.mark.asyncio
async def test_search_result_has_canonical_url() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={"src/app.py": "data"})
    response = await svc.search("owner/repo", "data")
    url = str(response.results[0].url)
    assert "github.com/owner/repo/blob/main/src/app.py" in url


@pytest.mark.asyncio
async def test_search_respects_limit() -> None:
    files = {f"file{i}.py": "match" for i in range(20)}
    svc, _ = _make_service(repos=["owner/repo"], files=files, max_results=5)
    response = await svc.search("owner/repo", "match", limit=5)
    assert len(response.results) <= 5


@pytest.mark.asyncio
async def test_search_enforces_max_results_cap() -> None:
    files = {f"file{i}.py": "match" for i in range(20)}
    svc, _ = _make_service(repos=["owner/repo"], files=files, max_results=3)
    response = await svc.search("owner/repo", "match", limit=100)
    assert len(response.results) <= 3


@pytest.mark.asyncio
async def test_search_denied_for_unknown_repo() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={})
    with pytest.raises(PermissionError):
        await svc.search("evil/repo", "query")


@pytest.mark.asyncio
async def test_search_empty_results() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={"file.py": "nothing"})
    response = await svc.search("owner/repo", "xyzzy_not_found")
    assert response.results == []


@pytest.mark.asyncio
async def test_search_file_extension_filter() -> None:
    files = {"src/app.py": "match", "src/app.ts": "match", "README.md": "match"}
    svc, provider = _make_service(repos=["owner/repo"], files=files)
    response = await svc.search("owner/repo", "match", file_extension="py")
    paths = {r.metadata.path for r in response.results}
    assert "src/app.py" in paths
    assert "src/app.ts" not in paths
    assert provider.last_search_extension == "py"


@pytest.mark.asyncio
async def test_search_file_extension_strips_leading_dot() -> None:
    files = {"src/app.py": "match"}
    svc, provider = _make_service(repos=["owner/repo"], files=files)
    await svc.search("owner/repo", "match", file_extension=".py")
    assert provider.last_search_extension == ".py"


# --- fetch ---


@pytest.mark.asyncio
async def test_fetch_returns_document() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={"README.md": "# Hello\nWorld"})
    doc_id = make_document_id("owner/repo", "README.md", "main")
    response = await svc.fetch(doc_id)
    assert response.document.id == doc_id
    assert "Hello" in response.document.text
    assert response.document.metadata.path == "README.md"
    assert response.document.metadata.repository == "owner/repo"


@pytest.mark.asyncio
async def test_fetch_url_is_canonical() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={"src/lib.py": "x = 1"})
    doc_id = make_document_id("owner/repo", "src/lib.py", "main")
    response = await svc.fetch(doc_id)
    url = str(response.document.url)
    assert "github.com/owner/repo/blob/main/src/lib.py" in url


@pytest.mark.asyncio
async def test_fetch_truncates_large_files() -> None:
    large_content = "x" * 200
    svc, _ = _make_service(
        repos=["owner/repo"], files={"big.py": large_content}, max_fetch_bytes=50
    )
    doc_id = make_document_id("owner/repo", "big.py", "main")
    response = await svc.fetch(doc_id)
    assert "truncated" in response.document.text
    assert len(response.document.text) < 200 + 200  # content + notice


@pytest.mark.asyncio
async def test_fetch_denied_for_unknown_repo() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={})
    doc_id = make_document_id("evil/repo", "file.py", "main")
    with pytest.raises(PermissionError):
        await svc.fetch(doc_id)


@pytest.mark.asyncio
async def test_fetch_invalid_id_raises() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={})
    with pytest.raises(ValueError):
        await svc.fetch("bad-id-no-separators")
