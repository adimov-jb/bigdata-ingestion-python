# Ingestão Python — Open-Meteo → bronze

Busca dados meteorológicos horários de 10 capitais brasileiras na API [Open-Meteo](https://open-meteo.com/), que é gratuita e não exige chave, e grava tudo em Parquet na camada bronze do S3.

```
Open-Meteo API ──> client.py ──> transform.py ──> writer.py ──> s3://<bronze>/open_meteo/weather_hourly/dt=YYYY-MM-DD/*.snappy.parquet
                                                                   │
                                  catalog.py (local) / Glue Crawler (AWS)
```

## Como funciona

- **Uma chamada por dia:** todas as cidades vão numa única requisição, com retry e backoff para os erros 429 e 5xx.
- **Endpoint escolhido pela data:**
  - Até 60 dias atrás: API de previsão.
  - Antes disso: API de arquivo histórico (ERA5), que tem alguns dias de atraso.
- **Schema fixo:** as colunas são sempre `city`, `latitude`, `longitude`, `observed_at` (UTC), as variáveis horárias, `ingested_at` e `dt`. Se a API deixar de mandar alguma variável, a execução falha em vez de gravar dados incompletos.
- **Idempotente:** o modo `overwrite_partitions` substitui só a partição do dia, então reprocessar uma data não duplica linhas.

Para mudar as cidades ou as variáveis, edite `src/ingestion/config.py`.

## Comandos

A plataforma local do repositório `bigdata-terraform` precisa estar no ar (`docker compose up -d` e `terraform apply` lá).

```bash
# Build da imagem (bigdata-ingestion:local)
docker compose build ingestion

# Ingerir um dia (sem --date: ontem, em UTC)
docker compose run --rm ingestion run --date 2026-09-29

# Registrar ou atualizar a tabela no catálogo local (equivale ao Glue Crawler)
docker compose run --rm ingestion register-local

# Testes e lint, sem acesso à rede
docker compose run --rm --build tests
```

### Consultar no Trino

```bash
docker compose -f ../Terraform/docker-compose.yml exec trino trino \
  --execute "SELECT dt, city, count(*) FROM hive.bronze.open_meteo_weather_hourly GROUP BY 1, 2 ORDER BY 1, 2"
```

## Variáveis de ambiente

| Variável | Local | AWS |
|---|---|---|
| `BRONZE_BUCKET` | `bigdata-local-bronze` | `bigdata-dev-bronze-<account_id>` |
| `AWS_ENDPOINT_URL` | `http://localstack:4566` | não definir |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | `test` | vêm da role da task ECS |
| `TRINO_HOST` / `TRINO_PORT` | `trino` / `8080` | não usado |

Os valores locais estão em `.env.local`, que é versionado porque não contém segredos.

## Estrutura

```
src/ingestion/
  config.py     cidades, variáveis e configuração por ambiente
  client.py     chamadas HTTP à Open-Meteo
  transform.py  resposta JSON → DataFrame com schema fixo
  writer.py     Parquet particionado no S3 (awswrangler)
  catalog.py    registro da tabela no Hive Metastore local via Trino
  cli.py        comandos run e register-local
tests/          pytest (HTTP mockado com responses, S3 mockado com moto)
```
