from __future__ import annotations

import pytest

from repo_research_mcp.github_provider import (
    DirectoryEntry,
    FileContent,
    FileMatch,
    RepositoryInfo,
    RepositoryProvider,
)
from repo_research_mcp.ids import make_document_id
from repo_research_mcp.research import RepositoryResearchService, _identify_key_files, _result_score
from repo_research_mcp.settings import Settings


class InMemoryProvider(RepositoryProvider):
    """Simple in-memory provider for tests."""

    def __init__(
        self,
        files: dict[str, str],
        description: str | None = None,
    ) -> None:
        self._files = files
        self._description = description
        self.last_search_extension: str | None = None
        self.last_search_language: str | None = None

    async def search_code(
        self,
        owner: str,
        repo: str,
        query: str,
        limit: int,
        file_extension: str | None = None,
        language: str | None = None,
    ) -> list[FileMatch]:
        self.last_search_extension = file_extension
        self.last_search_language = language
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

    async def fetch_repository_info(self, owner: str, repo: str) -> RepositoryInfo:
        return RepositoryInfo(
            full_name=f"{owner}/{repo}",
            description=self._description,
            default_branch="main",
            stars=42,
            forks=7,
            language="Python",
            topics=["mcp", "research"],
            html_url=f"https://github.com/{owner}/{repo}",
            size_kb=100,
        )

    async def fetch_tree(
        self, owner: str, repo: str, ref: str
    ) -> tuple[list[str], bool]:
        return sorted(self._files.keys()), False

    async def fetch_readme(
        self, owner: str, repo: str, ref: str, max_bytes: int
    ) -> str | None:
        content = self._files.get("README.md")
        if content is None:
            return None
        return content[:max_bytes]

    async def list_directory(
        self, owner: str, repo: str, path: str, ref: str
    ) -> list[DirectoryEntry]:
        prefix = (path.rstrip("/") + "/") if path else ""
        entries: list[DirectoryEntry] = []
        seen_dirs: set[str] = set()

        for file_path in self._files:
            if not file_path.startswith(prefix):
                continue
            relative = file_path[len(prefix):]
            parts = relative.split("/")

            if len(parts) == 1:
                entries.append(
                    DirectoryEntry(
                        name=parts[0],
                        path=file_path,
                        type="file",
                        sha="deadbeef",
                        size=len(self._files[file_path]),
                        html_url=f"https://github.com/{owner}/{repo}/blob/{ref}/{file_path}",
                    )
                )
            else:
                dir_name = parts[0]
                dir_path = prefix + dir_name
                if dir_path not in seen_dirs:
                    seen_dirs.add(dir_path)
                    entries.append(
                        DirectoryEntry(
                            name=dir_name,
                            path=dir_path,
                            type="dir",
                            sha=None,
                            size=None,
                            html_url=f"https://github.com/{owner}/{repo}/tree/{ref}/{dir_path}",
                        )
                    )

        entries.sort(key=lambda e: (e.type == "file", e.name.lower()))
        return entries


def _make_service(
    repos: list[str],
    files: dict[str, str],
    max_results: int = 10,
    max_fetch_bytes: int = 100_000,
    description: str | None = None,
) -> tuple[RepositoryResearchService, InMemoryProvider]:
    settings = Settings(
        allowed_repositories=repos,
        max_search_results=max_results,
        max_fetch_bytes=max_fetch_bytes,
    )
    provider = InMemoryProvider(files, description=description)
    return RepositoryResearchService(settings, provider=provider), provider


# --- _result_score ---


def test_result_score_readme_highest() -> None:
    assert _result_score("README.md") == 3
    assert _result_score("docs/ARCHITECTURE.md") == 3


def test_result_score_docs_dir() -> None:
    assert _result_score("docs/guide.md") == 2
    assert _result_score(".github/workflows/ci.yml") == 2


def test_result_score_root_file() -> None:
    assert _result_score("pyproject.toml") == 1


def test_result_score_nested_source() -> None:
    assert _result_score("src/deep/file.py") == 0


# --- _identify_key_files ---


def test_identify_key_files_finds_readme() -> None:
    tree = ["README.md", "src/main.py", "pyproject.toml"]
    keys = _identify_key_files(tree)
    assert "README.md" in keys
    assert "pyproject.toml" in keys
    assert "src/main.py" not in keys


def test_identify_key_files_case_insensitive() -> None:
    tree = ["readme.md", "CHANGELOG.md", "Makefile"]
    keys = _identify_key_files(tree)
    assert "readme.md" in keys
    assert "CHANGELOG.md" in keys
    assert "Makefile" in keys


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
    assert response.results[0].id == make_document_id("owner/repo", "file.py", "main")


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
async def test_search_language_filter_passed_to_provider() -> None:
    svc, provider = _make_service(repos=["owner/repo"], files={"app.py": "match"})
    await svc.search("owner/repo", "match", language="Python")
    assert provider.last_search_language == "Python"


@pytest.mark.asyncio
async def test_search_results_ranked_docs_first() -> None:
    files = {
        "src/deep/helper.py": "hello",
        "README.md": "hello",
        "docs/guide.md": "hello",
    }
    svc, _ = _make_service(repos=["owner/repo"], files=files)
    response = await svc.search("owner/repo", "hello")
    paths = [r.metadata.path for r in response.results]
    readme_idx = paths.index("README.md")
    helper_idx = paths.index("src/deep/helper.py")
    assert readme_idx < helper_idx


@pytest.mark.asyncio
async def test_search_snippet_fallback_when_empty() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={"src/app.py": "match"})

    class NoSnippetProvider(InMemoryProvider):
        async def search_code(
            self,
            owner: str,
            repo: str,
            query: str,
            limit: int,
            file_extension: str | None = None,
            language: str | None = None,
        ) -> list[FileMatch]:
            results = await super().search_code(
                owner, repo, query, limit,
                file_extension=file_extension, language=language,
            )
            for r in results:
                r.snippet = ""
            return results

    svc._provider = NoSnippetProvider({"src/app.py": "match"})
    response = await svc.search("owner/repo", "match")
    assert response.results[0].text.startswith("[matched by filename:")


# --- fetch ---


@pytest.mark.asyncio
async def test_fetch_returns_document() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={"README.md": "# Hello\nWorld"})
    doc_id = make_document_id("owner/repo", "README.md", "main")
    response = await svc.fetch(doc_id)
    assert response.document.id == doc_id
    assert "Hello" in response.document.text
    assert response.document.metadata.path == "README.md"


@pytest.mark.asyncio
async def test_fetch_url_is_canonical() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={"src/lib.py": "x = 1"})
    doc_id = make_document_id("owner/repo", "src/lib.py", "main")
    response = await svc.fetch(doc_id)
    assert "github.com/owner/repo/blob/main/src/lib.py" in str(response.document.url)


@pytest.mark.asyncio
async def test_fetch_truncates_large_files() -> None:
    large_content = "x" * 200
    svc, _ = _make_service(
        repos=["owner/repo"], files={"big.py": large_content}, max_fetch_bytes=50
    )
    doc_id = make_document_id("owner/repo", "big.py", "main")
    response = await svc.fetch(doc_id)
    assert "truncated" in response.document.text


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


# --- repository_overview ---


@pytest.mark.asyncio
async def test_overview_returns_metadata() -> None:
    svc, _ = _make_service(
        repos=["owner/repo"],
        files={"README.md": "# Hello"},
        description="A test repo",
    )
    response = await svc.repository_overview("owner/repo")
    ov = response.overview
    assert ov.repository == "owner/repo"
    assert ov.description == "A test repo"
    assert ov.stars == 42
    assert ov.language == "Python"
    assert "mcp" in ov.topics


@pytest.mark.asyncio
async def test_overview_url_is_canonical() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={})
    response = await svc.repository_overview("owner/repo")
    assert "github.com/owner/repo" in str(response.overview.url)


@pytest.mark.asyncio
async def test_overview_file_tree_returned() -> None:
    files = {"README.md": "hi", "src/app.py": "x = 1", "pyproject.toml": "[project]"}
    svc, _ = _make_service(repos=["owner/repo"], files=files)
    response = await svc.repository_overview("owner/repo")
    assert set(response.overview.file_tree) == set(files.keys())


@pytest.mark.asyncio
async def test_overview_key_files_identified() -> None:
    files = {"README.md": "hi", "src/app.py": "x = 1", "pyproject.toml": "[project]"}
    svc, _ = _make_service(repos=["owner/repo"], files=files)
    response = await svc.repository_overview("owner/repo")
    key = response.overview.key_files
    assert "README.md" in key
    assert "pyproject.toml" in key
    assert "src/app.py" not in key


@pytest.mark.asyncio
async def test_overview_readme_excerpt() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={"README.md": "# Hello World"})
    response = await svc.repository_overview("owner/repo")
    assert "Hello World" in (response.overview.readme_excerpt or "")


@pytest.mark.asyncio
async def test_overview_no_readme() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={"src/app.py": "x = 1"})
    response = await svc.repository_overview("owner/repo")
    assert response.overview.readme_excerpt is None


@pytest.mark.asyncio
async def test_overview_denied_for_unknown_repo() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={})
    with pytest.raises(PermissionError):
        await svc.repository_overview("evil/repo")


# --- list_files ---


@pytest.mark.asyncio
async def test_list_files_root_returns_top_level() -> None:
    files = {"README.md": "hi", "src/app.py": "x", "src/utils.py": "y"}
    svc, _ = _make_service(repos=["owner/repo"], files=files)
    response = await svc.list_files("owner/repo")
    names = {e.name for e in response.entries}
    assert "README.md" in names
    assert "src" in names
    assert "app.py" not in names


@pytest.mark.asyncio
async def test_list_files_subdirectory() -> None:
    files = {"src/app.py": "x", "src/utils.py": "y", "src/sub/deep.py": "z"}
    svc, _ = _make_service(repos=["owner/repo"], files=files)
    response = await svc.list_files("owner/repo", path="src")
    names = {e.name for e in response.entries}
    assert "app.py" in names
    assert "utils.py" in names
    assert "sub" in names
    assert "deep.py" not in names


@pytest.mark.asyncio
async def test_list_files_dirs_before_files() -> None:
    files = {"src/app.py": "x", "src/lib/mod.py": "y", "README.md": "r"}
    svc, _ = _make_service(repos=["owner/repo"], files=files)
    response = await svc.list_files("owner/repo", path="src")
    types = [e.type for e in response.entries]
    # dirs should come before files
    first_file = next(i for i, t in enumerate(types) if t == "file")
    last_dir = max((i for i, t in enumerate(types) if t == "dir"), default=-1)
    assert last_dir < first_file


@pytest.mark.asyncio
async def test_list_files_entry_has_canonical_url() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={"docs/guide.md": "hi"})
    response = await svc.list_files("owner/repo", path="docs")
    file_entry = next(e for e in response.entries if e.type == "file")
    assert "github.com/owner/repo/blob/main/docs/guide.md" in str(file_entry.url)


@pytest.mark.asyncio
async def test_list_files_response_metadata() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={"src/app.py": "x"})
    response = await svc.list_files("owner/repo", path="src", ref="develop")
    assert response.repository == "owner/repo"
    assert response.path == "src"
    assert response.ref == "develop"


@pytest.mark.asyncio
async def test_list_files_denied_for_unknown_repo() -> None:
    svc, _ = _make_service(repos=["owner/repo"], files={})
    with pytest.raises(PermissionError):
        await svc.list_files("evil/repo")
