from __future__ import annotations

import asyncio
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

_GITHUB_API = "https://api.github.com"
_ACCEPT_JSON = "application/vnd.github+json"
_ACCEPT_TEXT_MATCH = "application/vnd.github.text-match+json"
_SNIPPET_MAX = 500
_MAX_RETRIES = 3
_RETRY_STATUSES = {429, 503}


@dataclass
class FileMatch:
    path: str
    sha: str
    html_url: str
    snippet: str


@dataclass
class FileContent:
    path: str
    sha: str
    html_url: str
    text: str
    size: int
    truncated: bool = field(default=False)


class RepositoryProvider(ABC):
    """Abstract read-only repository content provider."""

    @abstractmethod
    async def search_code(
        self,
        owner: str,
        repo: str,
        query: str,
        limit: int,
        file_extension: str | None = None,
    ) -> list[FileMatch]: ...

    @abstractmethod
    async def fetch_file(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str,
        max_bytes: int,
    ) -> FileContent: ...

    async def aclose(self) -> None:  # noqa: B027 — default no-op for providers without resources
        pass


class GitHubProvider(RepositoryProvider):
    """Read-only GitHub REST API provider with rate-limit retry."""

    def __init__(self, token: str | None = None, base_url: str = _GITHUB_API) -> None:
        headers: dict[str, str] = {"X-GitHub-Api-Version": "2022-11-28"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, **kwargs: Any) -> httpx.Response:
        last_exc: httpx.HTTPStatusError | None = None
        for attempt in range(_MAX_RETRIES):
            response = await self._client.get(path, **kwargs)
            if response.status_code not in _RETRY_STATUSES:
                response.raise_for_status()
                return response
            retry_after = int(response.headers.get("Retry-After", 2 ** (attempt + 1)))
            wait = min(retry_after, 60)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                last_exc = exc
            await asyncio.sleep(wait)
        if last_exc:
            raise last_exc
        response.raise_for_status()
        return response

    async def search_code(
        self,
        owner: str,
        repo: str,
        query: str,
        limit: int,
        file_extension: str | None = None,
    ) -> list[FileMatch]:
        q = f"{query} repo:{owner}/{repo}"
        if file_extension:
            ext = file_extension.lstrip(".")
            q = f"{q} extension:{ext}"

        response = await self._get(
            "/search/code",
            params={"q": q, "per_page": min(limit, 30)},
            headers={"Accept": _ACCEPT_TEXT_MATCH},
        )
        data = response.json()

        results: list[FileMatch] = []
        for item in data.get("items", []):
            results.append(
                FileMatch(
                    path=item["path"],
                    sha=item["sha"],
                    html_url=item["html_url"],
                    snippet=_extract_snippet(item),
                )
            )
        return results

    async def fetch_file(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str,
        max_bytes: int,
    ) -> FileContent:
        response = await self._get(
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
            headers={"Accept": _ACCEPT_JSON},
        )
        data = response.json()

        if data.get("type") != "file":
            raise ValueError(f"path is not a file: {path!r}")

        size: int = data.get("size", 0)
        raw = base64.b64decode(data.get("content", "").replace("\n", ""))
        truncated = len(raw) > max_bytes
        text = raw[:max_bytes].decode("utf-8", errors="replace")

        return FileContent(
            path=data["path"],
            sha=data["sha"],
            html_url=data["html_url"],
            text=text,
            size=size,
            truncated=truncated,
        )


def _extract_snippet(item: dict) -> str:  # type: ignore[type-arg]
    for match in item.get("text_matches", []):
        fragment: str = match.get("fragment", "")
        if fragment:
            return fragment[:_SNIPPET_MAX]
    return ""
