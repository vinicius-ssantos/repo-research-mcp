FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir --prefix=/install .


FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /install /usr/local

ENV REPO_RESEARCH_ALLOWED_REPOSITORIES="[]"

ENTRYPOINT ["repo-research-mcp"]
