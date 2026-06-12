from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="REPO_RESEARCH_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    allowed_repositories: list[str] = Field(default_factory=list)
    github_token: str | None = None
    default_ref: str = "main"
    max_search_results: int = Field(default=10, ge=1, le=100)
    max_fetch_bytes: int = Field(default=100_000, ge=1)
    cache_ttl_seconds: float = Field(default=300.0, ge=0)
    log_format: Literal["json", "text"] = "json"
