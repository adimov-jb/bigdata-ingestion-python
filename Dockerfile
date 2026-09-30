FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src

# Imagem executada pelo Airflow (DockerOperator localmente, ECS na AWS).
FROM base AS runtime
RUN pip install . && useradd --system --uid 10001 app
USER app
ENTRYPOINT ["ingestion"]
CMD ["--help"]

# Imagem de testes: lint + pytest, sem acesso à rede.
FROM base AS test
RUN pip install ".[dev]"
COPY tests ./tests
CMD ["sh", "-c", "ruff check src tests && ruff format --check src tests && pytest -q"]
