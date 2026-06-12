from __future__ import annotations

_SEPARATOR = "::"


def make_document_id(repository: str, path: str, ref: str = "main") -> str:
    """Create a stable document ID for search/fetch round-trips."""

    return _SEPARATOR.join([repository, ref, path])


def parse_document_id(document_id: str) -> tuple[str, str, str]:
    """Parse a document ID into repository, ref, and path."""

    parts = document_id.split(_SEPARATOR, 2)
    if len(parts) != 3 or not all(parts):
        raise ValueError("invalid document id")
    repository, ref, path = parts
    return repository, ref, path
