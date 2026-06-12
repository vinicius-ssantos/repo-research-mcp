from __future__ import annotations

import pytest

from repo_research_mcp.ids import make_document_id, parse_document_id


def test_roundtrip() -> None:
    doc_id = make_document_id("owner/repo", "src/main.py", "main")
    repository, ref, path = parse_document_id(doc_id)
    assert repository == "owner/repo"
    assert ref == "main"
    assert path == "src/main.py"


def test_default_ref() -> None:
    doc_id = make_document_id("owner/repo", "README.md")
    _, ref, _ = parse_document_id(doc_id)
    assert ref == "main"


def test_nested_path() -> None:
    doc_id = make_document_id("owner/repo", "a/b/c/file.py", "develop")
    repository, ref, path = parse_document_id(doc_id)
    assert repository == "owner/repo"
    assert ref == "develop"
    assert path == "a/b/c/file.py"



def test_invalid_id_too_few_parts() -> None:
    with pytest.raises(ValueError, match="invalid document id"):
        parse_document_id("owner/repo::main")


def test_invalid_id_empty_string() -> None:
    with pytest.raises(ValueError, match="invalid document id"):
        parse_document_id("")


def test_invalid_id_empty_parts() -> None:
    with pytest.raises(ValueError, match="invalid document id"):
        parse_document_id(":::")
