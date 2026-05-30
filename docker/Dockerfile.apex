FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src ./src
COPY skills ./skills
COPY scripts ./scripts
COPY .cursor/skills ./.cursor/skills

RUN uv sync --frozen

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "apex_ledger.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
