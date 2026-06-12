from __future__ import annotations

from collections.abc import Iterable

from repo_research_mcp.models import RepositoryRef


class RepositoryAllowlist:
    """Allowlist for repositories that can be searched or fetched."""

    def __init__(self, repositories: Iterable[str]) -> None:
        self._repositories = {self._normalize(repository) for repository in repositories if repository.strip()}

    @staticmethod
    def _normalize(repository: str) -> str:
        normalized = repository.strip().lower()
        if normalized.count("/") != 1:
            raise ValueError(f"invalid repository reference: {repository!r}")
        owner, repo = normalized.split("/", 1)
        if not owner or not repo:
            raise ValueError(f"invalid repository reference: {repository!r}")
        return normalized

    def contains(self, repository: str) -> bool:
        return self._normalize(repository) in self._repositories

    def require(self, repository: str) -> RepositoryRef:
        normalized = self._normalize(repository)
        if normalized not in self._repositories:
            raise PermissionError(f"repository is not allowed: {repository}")
        owner, repo = normalized.split("/", 1)
        return RepositoryRef(owner=owner, repo=repo)

    def list(self) -> list[str]:
        return sorted(self._repositories)
