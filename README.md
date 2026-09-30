# Ingestão Python → bronze

Ingere fontes externas para a camada bronze do S3 em Parquet particionado por dia. Cada fonte é um módulo independente em `src/ingestion/sources/`. O núcleo é comum a todas e cuida da validação de schema, dos metadados, da gravação, do catálogo e do CLI.

```
            ┌─ sources/open_meteo ─┐
extract ───>│  sources/<outra>     │──> pipeline.py ──> writer.py ──> s3://<bronze>/<dataset>/dt=YYYY-MM-DD/*.snappy.parquet
            └──────────────────────┘   (schema + ingested_at + dt)          │
                                                     catalog.py (local) / Glue Crawler (AWS)
```

## Fontes

| Fonte | Tabela | Descrição |
|---|---|---|
| `open_meteo` | `bronze.open_meteo_weather_hourly` | Tempo horário de 10 capitais brasileiras na [Open-Meteo](https://open-meteo.com/), uma API gratuita e sem chave |
| `open_meteo_locations` | `bronze.open_meteo_locations` | Snapshot diário das cidades monitoradas, com UF, região e coordenadas. Não chama a API |

A lista de cidades fica só em `src/ingestion/sources/open_meteo/config.py`. Para incluir uma cidade, adicione-a ali, com UF e região. O dbt monta a `dim_city` a partir de `open_meteo_locations`, então não há outra lista para atualizar.

`ingestion list` mostra as fontes registradas na imagem.

## Garantias do núcleo

- **Execução isolada:** `run` sem nomes executa todas as fontes, uma de cada vez. Se uma falha, as outras continuam, e o comando termina com código 1 listando as que falharam.
- **Schema fixo:** o DataFrame que a fonte devolve precisa ter exatamente as colunas declaradas em `columns`. Se faltar ou sobrar coluna, a execução falha em vez de gravar dados incompletos.
- **Metadados padronizados:** toda tabela bronze recebe `ingested_at` (UTC, sem timezone) e `dt` (a partição).
- **Idempotente:** o modo `overwrite_partitions` substitui só a partição do dia, então reprocessar uma data não duplica linhas.
- **Catálogo derivado:** o DDL da tabela no Hive local sai das colunas declaradas na fonte.

## Comandos

A plataforma local do repositório `bigdata-terraform` precisa estar no ar (`docker compose up -d` e `terraform apply` lá).

```bash
# Build da imagem (bigdata-ingestion:local)
docker compose build ingestion

# Fontes disponíveis
docker compose run --rm ingestion list

# Ingerir um dia de todas as fontes (sem --date: ontem, em UTC)
docker compose run --rm ingestion run --date 2026-09-29

# Ingerir só algumas fontes
docker compose run --rm ingestion run open_meteo --date 2026-09-29

# Registrar ou atualizar as tabelas no catálogo local (equivale ao Glue Crawler);
# também aceita nomes de fontes
docker compose run --rm ingestion register-local

# Testes e lint, sem acesso à rede
docker compose run --rm --build tests
```

### Consultar no Trino

```bash
docker compose -f ../Terraform/docker-compose.yml exec trino trino \
  --execute "SELECT dt, city, count(*) FROM hive.bronze.open_meteo_weather_hourly GROUP BY 1, 2 ORDER BY 1, 2"
```

## Como adicionar uma fonte

1. Crie `src/ingestion/sources/<nome>/` e separe cliente, transformação e configuração, como em `open_meteo/`. Para APIs, use `ingestion.http.build_session()`, que já tem retry e backoff.
2. No `__init__.py` da pasta, exponha um `SOURCE`:

   ```python
   SOURCE = Source(
       name="minha_fonte",                   # nome no CLI
       description="O que a fonte traz",
       dataset="minha_fonte/entidade",       # prefixo no bucket bronze
       table="minha_fonte_entidade",         # tabela em hive.bronze
       columns=(Column("id", "bigint"), Column("valor", "double")),  # sem ingested_at/dt
       extract=extract,                      # (date) -> DataFrame com essas colunas
   )
   ```

3. Inclua o `SOURCE` em `_ALL`, no arquivo `src/ingestion/sources/__init__.py`.
4. Escreva os testes em `tests/test_<nome>_*.py`, com HTTP mockado via `responses`.

Credenciais específicas de uma fonte, como uma API key, devem ser lidas de variáveis de ambiente dentro do `extract`, e não em import. Assim uma chave ausente derruba só aquela fonte.

Se o schema de uma fonte mudar, `register-local` não altera uma tabela que já existe (`CREATE TABLE IF NOT EXISTS`). Nesse caso, faça `DROP TABLE hive.bronze.<tabela>` antes. A tabela é externa, então os dados no S3 são preservados.

## CI

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda em todo PR e em todo push para a `main`, com o mesmo comando de testes da seção anterior.

## Variáveis de ambiente

| Variável | Local | AWS |
|---|---|---|
| `BRONZE_BUCKET` | `bigdata-local-bronze` | `bigdata-dev-bronze-<account_id>` |
| `AWS_ENDPOINT_URL` | `http://localstack:4566` | não definir |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | `test` | vêm da role da task ECS |
| `TRINO_HOST` / `TRINO_PORT` | `trino` / `8080` | não usado |

Localmente, todas vêm de `platform/local.env`, gerado pelo `terraform apply` do repositório `bigdata-terraform`. O `docker-compose.yml` carrega esse arquivo, então este repositório não guarda cópia desses valores. Sem ele, o `run` falha com uma mensagem que explica como gerá-lo.

## Estrutura

```
src/ingestion/
  source.py       contrato Source/Column e colunas de metadados
  pipeline.py     extract → validação de schema → metadados → bronze
  writer.py       Parquet particionado no S3 (awswrangler)
  catalog.py      registro das tabelas no Hive Metastore local via Trino
  http.py         sessão HTTP com retry, compartilhada entre fontes
  settings.py     configuração por ambiente
  cli.py          comandos list, run e register-local
  sources/
    __init__.py   registro das fontes
    open_meteo/   config, client, transform e SOURCE
tests/            pytest (HTTP mockado com responses, S3 mockado com moto)
```
