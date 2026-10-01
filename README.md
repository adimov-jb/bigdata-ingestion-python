# bigdata-ingestion-python — ingestão das fontes para a bronze

Framework de ingestão de várias fontes para a camada bronze do data lake. Hoje são cinco fontes de três APIs: Open-Meteo (clima), Rest Countries v5 (países) e Banco Mundial (indicadores socioeconômicos). Tudo é gravado em Parquet particionado por dia no S3.

Cada fonte é um módulo independente em `src/ingestion/sources/` e roda isolada: a falha de uma não afeta as outras. O núcleo é comum a todas e cuida da validação de schema, dos metadados (`ingested_at`, `dt`), da gravação idempotente, do registro no catálogo e do CLI.

## A plataforma

Este repositório é uma das quatro partes da plataforma de dados **bigdata**. Ela coleta dados públicos de APIs, organiza tudo num data lake em camadas (bronze → silver → gold) e entrega tabelas analíticas validadas. Tudo roda localmente em Docker, com LocalStack, Hive Metastore e Trino no lugar de S3, Glue e Athena, e está preparado para a AWS.

| Repositório | Papel |
|---|---|
| [bigdata-terraform](https://github.com/adimov-jb/bigdata-terraform) | Infraestrutura (AWS e local), contrato da plataforma, operação (`scripts/platform.sh`) e runbook |
| **bigdata-ingestion-python** (este) | Ingestão das APIs para a camada bronze (Parquet no S3) |
| [bigdata-dbt-modeling](https://github.com/adimov-jb/bigdata-dbt-modeling) | Camadas silver e gold (Iceberg), relacionamento entre fontes e validação de qualidade |
| [bigdata-airflow-dags](https://github.com/adimov-jb/bigdata-airflow-dags) | Orquestração diária, alertas por e-mail e monitoramento de freshness |

| Domínio | Fontes | Principais tabelas na gold |
|---|---|---|
| Clima | [Open-Meteo](https://open-meteo.com/): tempo horário de 10 capitais brasileiras | `fct_weather_daily`, `dim_city` |
| Países | [Rest Countries v5](https://restcountries.com/) e [Banco Mundial](https://data.worldbank.org/): atributos dos países e indicadores socioeconômicos (PIB, inflação, expectativa de vida, pobreza, população) | `dim_country`, `fct_country_indicators_yearly`, `dq_indicator_coverage` |

Para subir e operar tudo junto, use o `scripts/platform.sh up` do repositório `bigdata-terraform`. Os problemas conhecidos estão no [RUNBOOK](https://github.com/adimov-jb/bigdata-terraform/blob/main/RUNBOOK.md).

## Arquitetura

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
| `rest_countries` | `bronze.rest_countries` | Snapshot diário dos países e territórios da [Rest Countries v5](https://restcountries.com/docs/countries): códigos ISO, população, área, capital, moedas, idiomas e fusos. **Exige chave de API** (veja abaixo) |
| `world_bank_indicators` | `bronze.world_bank_indicators` | Snapshot diário da série desde 2000 de indicadores do [Banco Mundial](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392): PIB, inflação, expectativa de vida, pobreza e população. Formato longo: país × indicador × ano |
| `world_bank_countries` | `bronze.world_bank_countries` | Países e agregados do Banco Mundial, com região, faixa de renda e `is_aggregate` para separar regiões e faixas de renda dos países |
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

O jeito mais simples de subir e operar os quatro repositórios juntos é o `scripts/platform.sh` do repositório `bigdata-terraform` (`up`, `build`, `status` e `reset`). Problemas comuns e como resolvê-los estão no [RUNBOOK](https://github.com/adimov-jb/bigdata-terraform/blob/main/RUNBOOK.md).

O `scripts/platform.sh build` grava o commit deste repositório na imagem (label `org.opencontainers.image.revision`), e toda execução registra esse commit na primeira linha do log. Um `docker compose build` direto grava `dev`.

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

**Chaves de API no ambiente local:** ficam em `platform/secrets.env`, no repositório `bigdata-terraform`. Esse arquivo é criado a partir de `platform/secrets.env.example` e não entra no git. O `docker-compose.yml` o carrega, e o Airflow repassa cada chave só para a task da fonte que a usa, sem mostrá-la nos logs. Na AWS, as chaves ficam no Secrets Manager. Hoje só a `rest_countries` usa chave (`REST_COUNTRIES_API_KEY`, plano gratuito em restcountries.com/sign-up).

**APIs que respondem erro com HTTP 200:** a Rest Countries (inclusive a v3.1 descontinuada) e o Banco Mundial devolvem erros com status 200. Os clientes conferem o formato da resposta e falham com a mensagem da API, em vez de gravar o erro como se fosse dado.

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
| `REST_COUNTRIES_API_KEY` | `platform/secrets.env` (fora do git) | Secrets Manager |

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
requirements.lock       versões exatas de todas as dependências da imagem
requirements-dev.lock   idem, com as ferramentas de teste
scripts/lock.sh         regenera os dois .lock a partir do pyproject.toml
```

O `pyproject.toml` define só os limites de versão. As imagens instalam os `.lock`, então builds feitos em dias diferentes geram a mesma imagem. Para atualizar as dependências, rode `scripts/lock.sh`, revise o diff e rode os testes.
