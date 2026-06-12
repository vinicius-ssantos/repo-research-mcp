from __future__ import annotations

import pytest

from repo_research_mcp.allowlist import RepositoryAllowlist


def test_contains_exact_match() -> None:
    al = RepositoryAllowlist(["owner/repo"])
    assert al.contains("owner/repo")


def test_contains_case_insensitive() -> None:
    al = RepositoryAllowlist(["owner/repo"])
    assert al.contains("OWNER/REPO")
    assert al.contains("Owner/Repo")


def test_not_contains() -> None:
    al = RepositoryAllowlist(["owner/repo"])
    assert not al.contains("other/repo")
    assert not al.contains("owner/other")


def test_require_returns_ref() -> None:
    al = RepositoryAllowlist(["owner/repo"])
    ref = al.require("owner/repo")
    assert ref.owner == "owner"
    assert ref.repo == "repo"
    assert ref.full_name == "owner/repo"


def test_require_not_allowed_raises() -> None:
    al = RepositoryAllowlist(["owner/repo"])
    with pytest.raises(PermissionError, match="not allowed"):
        al.require("other/repo")


def test_invalid_format_raises() -> None:
    with pytest.raises(ValueError, match="invalid repository reference"):
        RepositoryAllowlist(["nodash"])


def test_invalid_empty_owner_raises() -> None:
    with pytest.raises(ValueError, match="invalid repository reference"):
        RepositoryAllowlist(["/repo"])


def test_invalid_empty_repo_raises() -> None:
    with pytest.raises(ValueError, match="invalid repository reference"):
        RepositoryAllowlist(["owner/"])


def test_empty_strings_are_skipped() -> None:
    al = RepositoryAllowlist(["owner/repo", "", "  "])
    assert al.list() == ["owner/repo"]


def test_list_sorted() -> None:
    al = RepositoryAllowlist(["z/repo", "a/repo", "m/repo"])
    assert al.list() == ["a/repo", "m/repo", "z/repo"]


def test_empty_allowlist_denies_all() -> None:
    al = RepositoryAllowlist([])
    with pytest.raises(PermissionError):
        al.require("owner/repo")
