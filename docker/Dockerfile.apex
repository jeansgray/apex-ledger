FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src ./src
COPY skills ./skills
COPY scripts ./scripts
COPY .cursor/skills ./.cursor/skills

COPY scripts/seed_personal_investor_simulation.py ./scripts/

RUN uv sync --frozen

COPY docker/apex-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
