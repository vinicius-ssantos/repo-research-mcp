from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class RepositoryRef(BaseModel):
    """A GitHub repository reference allowed for research."""

    owner: str = Field(min_length=1)
    repo: str = Field(min_length=1)

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


class DocumentMetadata(BaseModel):
    """Metadata attached to a search/fetch document."""

    repository: str
    path: str
    ref: str = "main"
    sha: str | None = None
    source: Literal["github"] = "github"
    extra: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Compact citable result returned by the search tool."""

    id: str
    title: str
    url: HttpUrl
    text: str
    metadata: DocumentMetadata


class FetchedDocument(BaseModel):
    """Full document returned by the fetch tool."""

    id: str
    title: str
    url: HttpUrl
    text: str
    metadata: DocumentMetadata


class SearchResponse(BaseModel):
    results: list[SearchResult]


class FetchResponse(BaseModel):
    document: FetchedDocument


class RepositoryOverview(BaseModel):
    """Repository overview returned by the repository_overview tool."""

    repository: str
    description: str | None
    default_branch: str
    url: HttpUrl
    stars: int
    forks: int
    language: str | None
    topics: list[str]
    file_count: int
    file_tree: list[str]
    key_files: list[str]
    readme_excerpt: str | None
    tree_truncated: bool


class RepositoryOverviewResponse(BaseModel):
    overview: RepositoryOverview


class FileEntry(BaseModel):
    """A single file or directory entry returned by the list_files tool."""

    name: str
    path: str
    type: Literal["file", "dir"]
    sha: str | None = None
    size: int | None = None
    url: HttpUrl


class ListFilesResponse(BaseModel):
    repository: str
    path: str
    ref: str
    entries: list[FileEntry]
