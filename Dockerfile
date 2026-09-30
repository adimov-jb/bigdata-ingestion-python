FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
# Versões exatas de todas as dependências (scripts/lock.sh); o pyproject.toml só define limites.
COPY requirements.lock requirements-dev.lock ./
COPY pyproject.toml README.md ./
COPY src ./src

# Imagem executada pelo Airflow (DockerOperator localmente, ECS na AWS).
FROM base AS runtime
RUN pip install -r requirements.lock \
    && pip install --no-deps . \
    && pip check \
    && useradd --system --uid 10001 app
# Commit do código na imagem: aparece no log de toda execução e no label OCI.
# scripts/platform.sh (repositório Terraform) passa o SHA no build; sem ele, fica "dev".
ARG GIT_SHA=dev
LABEL org.opencontainers.image.source="https://github.com/adimov-jb/bigdata-ingestion-python" \
      org.opencontainers.image.revision="${GIT_SHA}"
ENV BIGDATA_VERSION="${GIT_SHA}"
USER app
ENTRYPOINT ["ingestion"]
CMD ["--help"]

# Imagem de testes: lint + pytest, sem acesso à rede.
FROM base AS test
RUN pip install -r requirements-dev.lock \
    && pip install --no-deps . \
    && pip check
COPY tests ./tests
CMD ["sh", "-c", "ruff check src tests && ruff format --check src tests && pytest -q"]
