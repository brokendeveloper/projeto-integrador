# LicitaME — Engenharia de Dados

> Pipeline de dados, arquitetura Medallion (MongoDB), SQL, processamento Batch, observabilidade, Kafka roadmap, MCP Server e Chatbot Léo.

---

## Índice

1. [Visão Geral da Arquitetura de Dados](#1-visão-geral-da-arquitetura-de-dados)
2. [Camadas Medallion — Bronze, Silver, Gold no MongoDB](#2-camadas-medallion--bronze-silver-gold-no-mongodb)
3. [SQL — SQLite como Persistência Analítica Secundária](#3-sql--sqlite-como-persistência-analítica-secundária)
4. [Pipeline ETL — Ingestão da Camada Bronze](#4-pipeline-etl--ingestão-da-camada-bronze)
5. [Pipeline PySpark — Produção das Camadas Silver e Gold](#5-pipeline-pyspark--produção-das-camadas-silver-e-gold)
6. [Consumo das Camadas Gold — Analytics API](#6-consumo-das-camadas-gold--analytics-api)
7. [Batch vs Streaming — Decisão Arquitetural e Roadmap Kafka](#7-batch-vs-streaming--decisão-arquitetural-e-roadmap-kafka)
8. [Observabilidade e Gestão de Logs](#8-observabilidade-e-gestão-de-logs)
9. [MCP Server — Ferramentas como Protocolo](#9-mcp-server--ferramentas-como-protocolo)
10. [Chatbot Léo — Tool Calling com Claude](#10-chatbot-léo--tool-calling-com-claude)
11. [Erros Mapeados e Resiliência da Pipeline](#11-erros-mapeados-e-resiliência-da-pipeline)

---

## 1. Visão Geral da Arquitetura de Dados

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FONTE EXTERNA                                     │
│           API PNCP — pncp.gov.br/api/consulta/v1/contratos                  │
│                  HTTP REST · paginação · retry exponencial                   │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │     ETL PIPELINE     │
                    │  extractor           │
                    │  transformer         │  ← normaliza datas, valores,
                    │  loader              │    texto; adiciona _etl_timestamp
                    └──────┬──────────────┘
                           │
          ┌────────────────┼────────────────────────────┐
          ▼                ▼                             ▼
┌──────────────────┐  ┌──────────────────┐   ┌─────────────────────────┐
│  BRONZE (MongoDB)│  │   SQL (SQLite)   │   │   Kafka Producer        │
│  contratos       │  │  db/contratos.db │   │   kafka/producer.py     │
│  JSON normalizado│  │  INSERT OR IGNORE│   │   tópico:               │
│  + _etl_timestamp│  └──────────────────┘   │   pncp.contratos.novos  │
└────────┬─────────┘                         └────────────┬────────────┘
         │                                                 │
         │ pymongo→pandas→Spark                  ┌─────────┴──────────┐
         │ flatten orgaoEntidade                 ▼                    ▼
         ▼                              FastAPI Consumer      Spark Streaming
┌────────────────────────────┐          kafka/consumer.py    spark/streaming.py
│     PYSPARK local[*]       │          (asyncio no lifespan) (spark-submit)
│  pyspark_transform.py      │                 │                    │
│  flatten · stats · filtros │         [1] Silver upsert     Silver append
│  Dedup: índice único upstream│        [2] Gold MEI upsert
└──────┬──────────────┬──────┘         [3] Gold Top $inc
       │              │                [4] Alertas → notificacoes
       ▼              ▼
┌────────────┐  ┌──────────────┐
│   SILVER   │  │   GOLD CSV   │   ← atualizados pelo batch E pelo streaming
│  MongoDB   │  │ spark/output/│     (batch: snapshot completo)
│  (drop+ins)│  │ contratos_   │     (streaming: upsert incremental)
└────────────┘  │ mei.csv etc  │
       │        └──────────────┘
       ▼
┌────────────────────┐  ┌────────────────────┐
│  GOLD (MongoDB)    │  │   Analytics API     │
│  gold_contratos_   │  │   GET /analytics/   │
│  mei · top_orgaos  │  │   spark            │
└────────────────────┘  └────────────────────┘
       │
       ▼
App Mobile · Chatbot Léo · MCP Server · Dashboard
```

---

## 2. Camadas Medallion — Bronze, Silver, Gold no MongoDB

A arquitetura segue o padrão **Medallion** com três camadas no MongoDB Atlas, mais um CSV Gold paralelo para consumo pela Analytics API.

---

### Bronze — `contratos`

| Atributo | Detalhe |
|----------|---------|
| Coleção MongoDB | `contratos` |
| Origem | API PNCP via ETL Pipeline |
| Deduplicação | Índice único em `numeroControlePNCP` + upsert bulk |
| Conteúdo | JSON da API PNCP com normalização mínima: datas em ISO 8601, valores como `float`, campos de texto com `.strip()`, campos nulos removidos |
| Metadados adicionados | `_etl_timestamp` (datetime UTC da ingestão), `_source: "pncp_api"` |
| Volume | 801 contratos (MVP) |
| Índices | `numeroControlePNCP` (unique, sparse) · `dataPublicacaoPncp` |

O Bronze é a base de toda a pipeline. A estrutura do `orgaoEntidade` é preservada como objeto aninhado nessa camada — o flatten ocorre apenas nas camadas seguintes.

```json
{
  "numeroControlePNCP": "04926214000174-1-000001/2024",
  "objetoContrato": "Aquisição de material de expediente",
  "valorInicial": 12500.0,
  "dataPublicacaoPncp": "2024-01-15T00:00:00+00:00",
  "orgaoEntidade": {
    "cnpj": "04926214000174",
    "razaoSocial": "Prefeitura Municipal de São Paulo"
  },
  "_etl_timestamp": "2025-06-01T10:30:00+00:00",
  "_source": "pncp_api"
}
```

---

### Silver — `silver_contratos`

| Atributo | Detalhe |
|----------|---------|
| Coleção MongoDB | `silver_contratos` |
| Origem | PySpark (`spark/pyspark_transform.py`) |
| Geração | Após cada execução do pipeline PySpark (via `POST /analytics/executar-spark` ou `python spark/pyspark_transform.py`) |
| Conteúdo | Todos os contratos com `orgaoEntidade` achatado em colunas planas |

Transformações aplicadas pelo PySpark antes da escrita Silver:

1. **Flatten de `orgaoEntidade`** — campo JSON aninhado explodido em colunas planas:
   - `orgao_cnpj` ← `orgaoEntidade.cnpj`
   - `orgao_nome` ← `orgaoEntidade.razaoSocial`

2. **Schema Spark inferido** — tipos Python/pandas convertidos para `StringType`, `DoubleType`, `DateType` pelo Spark. Garante tipagem consistente independente de variação nos documentos de origem.

3. **Estatísticas calculadas** — `summary()` com count, mean, stddev, min, 25%, 75%, max sobre `valorInicial`.

4. **Série temporal** — `substring(dataPublicacaoPncp, 1, 7)` para extração de mês.

```json
{
  "numeroControlePNCP": "04926214000174-1-000001/2024",
  "objetoContrato": "Aquisição de material de expediente",
  "valorInicial": 12500.0,
  "dataPublicacaoPncp": "2024-01-15T00:00:00+00:00",
  "orgao_cnpj": "04926214000174",
  "orgao_nome": "Prefeitura Municipal de São Paulo",
  "_etl_timestamp": "2025-06-01T10:30:00+00:00"
}
```

**Deduplicação**: não há step explícito de `dropDuplicates()` no PySpark porque o MongoDB já garantiu unicidade via índice `unique` em `numeroControlePNCP` na camada Bronze. O Spark recebe dados sem duplicatas.

---

### Gold — `gold_contratos_mei` e `gold_top_orgaos`

| Coleção | Conteúdo | Uso |
|---------|---------|-----|
| `gold_contratos_mei` | Contratos com `valorInicial > 0 AND valorInicial <= 80.000` — filtro MEI (LC 123/2006, Art. 48) | Chatbot Léo · Analytics API |
| `gold_top_orgaos` | Top 50 órgãos ordenados por `count` de contratos (groupBy + orderBy) | Dashboard · Analytics API · MCP tool `top_orgaos` |

Geradas a cada execução do PySpark, via `_salvar_camadas_mongodb()`. As coleções são **recriadas a cada run** (`drop()` + `insert_many()`), garantindo que sempre reflitam o estado atual do Bronze.

#### CSV Gold paralelo

Além das coleções MongoDB, o PySpark mantém os CSVs em `spark/output/` como camada Gold secundária para consumo por pandas sem conexão com MongoDB:

| Arquivo | Conteúdo |
|---------|---------|
| `contratos_mei.csv` | Mesma query do `gold_contratos_mei` |
| `top_orgaos.csv` | Mesmo dado do `gold_top_orgaos` |
| `contratos_completo.csv` | Todos os contratos Silver em formato plano |

---

## 3. SQL — SQLite como Persistência Analítica Secundária

O projeto possui uma camada SQL via **SQLite** (`db/contratos.db`), implementada em `etl/loader.py` pela classe `SQLiteLoader`.

### Por que SQLite?

O ETL grava em dois destinos simultaneamente:
- **MongoDB Atlas**: destino primário, operacional, consultado pela API
- **SQLite local**: destino secundário, para análise offline sem conectividade com o Atlas

### Estrutura da tabela

```sql
CREATE TABLE IF NOT EXISTS contratos (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_controle_pncp  TEXT    UNIQUE,
    objeto_contrato       TEXT,
    valor_inicial         REAL,
    data_publicacao_pncp  TEXT,
    data_vigencia_inicio  TEXT,
    data_vigencia_fim     TEXT,
    orgao_cnpj            TEXT,
    orgao_razao_social    TEXT,
    etl_timestamp         TEXT,
    source                TEXT
);
```

### Diferenças Bronze vs SQL

| Aspecto | Bronze (MongoDB) | SQLite |
|---------|-----------------|--------|
| Schema | Dinâmico (JSON) | Fixo (relacional) |
| `orgaoEntidade` | Objeto aninhado | Achatado em `orgao_cnpj` / `orgao_razao_social` |
| Deduplicação | Upsert por `numeroControlePNCP` | `INSERT OR IGNORE` com `UNIQUE` |
| Uso | API, PySpark, Chatbot | Análise offline, SQL ad-hoc |

O `SQLiteLoader` já faz o **flatten de `orgaoEntidade`** ao persistir:
```python
orgao = doc.get("orgaoEntidade") or {}
cursor.execute("INSERT OR IGNORE ...", (
    doc.get("numeroControlePNCP"),
    doc.get("objetoContrato"),
    doc.get("valorInicial"),
    orgao.get("cnpj"),         # orgao_cnpj
    orgao.get("razaoSocial"),  # orgao_razao_social
    ...
))
```

O SQLite aceita queries SQL convencionais para análise exploratória:
```sql
SELECT orgao_razao_social, COUNT(*) as total, AVG(valor_inicial) as media
FROM contratos
WHERE valor_inicial <= 80000
GROUP BY orgao_razao_social
ORDER BY total DESC
LIMIT 10;
```

---

## 4. Pipeline ETL — Ingestão da Camada Bronze

```
etl/pipeline.py  (ETLPipeline.run)
│
├── [1] PNCPExtractor.fetch_contratos(data_inicial, data_final)
│   ├── GET pncp.gov.br/api/consulta/v1/contratos?dataInicial=X&dataFinal=Y&pagina=1
│   ├── paginação automática até records < page_size
│   ├── retry exponencial: 3 tentativas, backoff 2–10s (tenacity)
│   └── retorna lista de dicts (JSON bruto da API)
│
├── PNCPExtractor.fetch_atas(data_inicial, data_final)
│   └── mesmo fluxo para /atas
│
├── [2] PNCPTransformer.transform(raw_records)
│   ├── datas → ISO 8601 (fromisoformat + timezone)
│   ├── valores monetários → float (remove "." e troca "," por ".")
│   ├── campos de texto → .strip()
│   ├── remove campos nulos ou vazios ("{k: v for ... if v is not None and v != ''}")
│   └── adiciona _etl_timestamp (UTC) e _source = "pncp_api"
│
├── [3] MongoLoader.load(transformed)
│   ├── bulk_write com UpdateOne(upsert=True) em lotes de 500
│   ├── chave única: {"numeroControlePNCP": doc["numeroControlePNCP"]}
│   ├── índice unique + sparse criado automaticamente na inicialização
│   └── loga: lote X/Y — N documentos upserted
│
└── [4] SQLiteLoader.load(transformed)
    ├── INSERT OR IGNORE por numero_controle_pncp UNIQUE
    ├── flatten de orgaoEntidade inline
    └── loga: N registros inseridos
```

### Idempotência

Rodar o ETL múltiplas vezes sobre o mesmo intervalo de datas **não duplica registros**:
- MongoDB: `UpdateOne(upsert=True)` atualiza se já existe, insere se não
- SQLite: `INSERT OR IGNORE` descarta silenciosamente duplicatas

---

## 5. Pipeline PySpark — Produção das Camadas Silver e Gold

```
spark/pyspark_transform.py  (main)
│
├── [1/5] _carregar_contratos_mongodb()
│   ├── pymongo.MongoClient → collection.find({}, projecao)
│   ├── flatten orgaoEntidade → colunas orgao_cnpj, orgao_nome no pandas DataFrame
│   └── retorna pd.DataFrame (Bronze lido e parcialmente normalizado)
│
├── [2/5] spark.createDataFrame(pdf)
│   └── Spark DataFrame com schema inferido automaticamente
│
├── [3/5] Transformações Silver
│   ├── df.printSchema()                             (diagnóstico)
│   ├── df.select(...).show(5, truncate=60)          (amostra)
│   ├── df.filter(valorInicial.isNotNull)
│   │   .select("valorInicial")
│   │   .summary("count","mean","stddev","min","25%","75%","max")
│   ├── df.groupBy("orgao_nome").count()
│   │   .orderBy(desc("count")).limit(10).show()
│   └── df.withColumn("mes", substring("dataPublicacaoPncp", 1, 7))
│       .groupBy("mes").count().orderBy("mes").show()
│
├── [4/5] Produção Gold (CSV)
│   ├── df_mei = df.filter(valorInicial > 0 AND <= 80000)
│   ├── pdf_mei.to_csv("spark/output/contratos_mei.csv")
│   ├── df_top = df.groupBy("orgao_nome").count().orderBy(desc).limit(50)
│   ├── pdf_top.to_csv("spark/output/top_orgaos.csv")
│   └── df.toPandas().to_csv("spark/output/contratos_completo.csv")
│
└── [5/5] _salvar_camadas_mongodb(pdf_completo, pdf_mei, pdf_top)
    ├── silver_contratos.drop() → insert_many(pdf_completo)
    ├── gold_contratos_mei.drop() → insert_many(pdf_mei)
    └── gold_top_orgaos.drop() → insert_many(pdf_top)
```

### Execução via API

```
POST /analytics/executar-spark          (autenticado, Bearer token)
│
├── asyncio.create_subprocess_exec(python, pyspark_transform.py)
├── asyncio.ensure_future(_aguardar_spark(proc))   ← não bloqueia
└── retorna imediatamente: { "status": "iniciado", "pid": X }

Em background:
_aguardar_spark(proc)
├── proc.communicate() → aguarda término
├── returncode != 0 → logger.error(stderr)
└── returncode == 0 → logger.info("concluído")
```

---

## 6. Consumo das Camadas Gold — Analytics API

A API oferece dois caminhos de consulta, complementares:

### Caminho A — MongoDB Aggregation (near-realtime)

Consulta direta ao MongoDB sem aguardar PySpark. Reflete o Bronze imediatamente após o ETL.

| Endpoint | O que faz | Coleção |
|----------|-----------|---------|
| `GET /analytics/estatisticas` | Total, média, max, min de `valorInicial` | `contratos` (Bronze) |
| `GET /analytics/top-orgaos` | Ranking por `groupBy orgaoEntidade.razaoSocial` | `contratos` (Bronze) |
| `GET /analytics/contratos-mei` | `find({valorInicial: {$lte: 80000}})` | `contratos` (Bronze) |

### Caminho B — CSV Gold (batch PySpark)

Lê os CSVs produzidos pelo PySpark. Reflete o estado da última execução do pipeline.

| Endpoint | O que retorna |
|----------|--------------|
| `GET /analytics/spark` | `SparkSummaryResponse`: total processado, last run timestamp, MEI stats (média/max/min), histograma em buckets de R$ 10k, top órgãos, amostra de 20 contratos MEI |

Se os CSVs não existem: `{ "disponivel": false }` sem erro.

### Por que dois caminhos?

| Aspecto | Aggregation (A) | CSV Gold (B) |
|---------|----------------|-------------|
| Latência | Sob demanda (segundos) | Depende da última run do Spark |
| Complexidade da query | MongoDB Aggregation | pandas read_csv |
| Dados | Sempre atuais | Estado do último batch |
| Uso ideal | Chatbot Léo, alertas | Dashboard analítico, relatórios |

---

## 7. Batch vs Streaming — Duas Pipelines Complementares

### Por que manter os dois modelos

O PNCP é uma API **pull-based de atualização periódica** — órgãos publicam em lotes. O batch ainda é a fonte primária de ingestão. O streaming foi adicionado como **camada complementar**, não substituto:

| Aspecto | Batch (PySpark) | Streaming (Kafka) |
|---------|----------------|-------------------|
| Frequência | Sob demanda / agendado | Em tempo real, por contrato |
| Silver | `drop()` + `insert_many()` (snapshot completo) | `updateOne(upsert=True)` incremental |
| Gold MEI | `drop()` + `insert_many()` (snapshot) | `updateOne(upsert=True)` incremental |
| Gold Top Órgãos | `groupBy().count()` full-recalc exato | `$inc` atômico acumulado |
| Alertas | — | ✅ Verificação imediata ao receber |
| Ideal para | Consistência total, relatórios | Latência mínima, alertas em tempo real |

---

### Arquitetura implementada

```
                           PNCP API
                               │
                       ETL Pipeline
                  (extractor → transformer)
                               │
             ┌─────────────────┼──────────────┐
             ▼                 ▼              ▼
       MongoDB Bronze       SQLite       Kafka Producer
        (contratos)        local       pncp.contratos.novos
       upsert batch      INSERT OR           │
                          IGNORE      ┌──────┴──────────────────┐
             │                        ▼                          ▼
             │               FastAPI Consumer           Spark Structured
             │               kafka/consumer.py          Streaming
             │               (asyncio task no           spark/streaming.py
             │                lifespan da API)          (spark-submit)
             │                        │                          │
             │           ┌────────────┼──────────┐              │
             │           ▼            ▼           ▼              ▼
             │     silver_contratos  gold_       gold_     silver_contratos
             │     (upsert)          contratos_  top_      (append)
             │                       mei         orgaos
             │                      (upsert)    ($inc)
             │
             ▼  (POST /analytics/executar-spark)
         PySpark
   pyspark_transform.py
             │
    ┌────────┼──────────┐
    ▼        ▼          ▼
 Silver   Gold MEI  Gold Top    ← MongoDB (drop+insert) + CSV
```

---

### Kafka Consumer — pipeline por mensagem (`kafka/consumer.py`)

Para cada contrato recebido do tópico, `_processar_contrato()` executa 4 etapas:

```
Mensagem Kafka (JSON)
        │
        ▼
[1] _gravar_silver()
    ├── flatten orgaoEntidade → orgao_cnpj, orgao_nome
    ├── remove _id e orgaoEntidade aninhado
    └── silver_contratos.update_one(upsert=True) por numeroControlePNCP
        │
        ▼
[2] _gravar_gold_mei()
    ├── valorInicial > 0 AND <= 80.000?
    │   ├── SIM → gold_contratos_mei.update_one(upsert=True)
    │   └── NÃO → skip
        │
        ▼
[3] _atualizar_gold_top_orgaos()
    └── gold_top_orgaos.update_one(
            {"orgao_nome": X},
            {"$inc": {"count": 1, "valor_total": valor}},
            upsert=True
        )
        │
        ▼
[4] _verificar_e_notificar()
    ├── itera db.alertas ({"ativo": True})
    ├── filtra por valor_max / cnae / uf
    └── match → db.notificacoes.insert_one(...)
```

### Ativação e configuração

O Kafka é **opcional** — todos os componentes são desativados silenciosamente quando `KAFKA_BOOTSTRAP_SERVERS` não está definido.

```bash
# Desenvolvimento local (docker-compose.kafka.yml)
docker compose -f docker-compose.kafka.yml up -d
# Kafka UI: http://localhost:8080

# Variáveis de ambiente
KAFKA_BOOTSTRAP_SERVERS=localhost:9092        # dev local
KAFKA_BOOTSTRAP_SERVERS=<URL Confluent Cloud> # produção
KAFKA_TOPIC_CONTRATOS=pncp.contratos.novos
KAFKA_GROUP_ID=licitame-alertas
```

**Para produção (SquareCloud):** configurar `KAFKA_BOOTSTRAP_SERVERS` no painel de variáveis de ambiente. O `squarecloud.app` não precisa de alterações — o consumer é iniciado automaticamente pelo lifespan da API quando a variável estiver presente.

### Spark Structured Streaming (`spark/streaming.py`)

Job alternativo de alto throughput — recomendado quando o volume de mensagens exigir paralelismo além do consumer asyncio:

```bash
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.2,\
             org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
  spark/streaming.py
```

Diferença do consumer FastAPI: o Spark Streaming escreve em `silver_contratos` com `outputMode="append"` (sem upsert), adequado para pipelines de alta ingestão onde duplicatas são aceitáveis antes de uma passagem batch.

### Roadmap restante

| Item | Status |
|------|--------|
| Producer (`kafka/producer.py`) | ✅ Implementado |
| Consumer completo Bronze→Silver→Gold→Alertas | ✅ Implementado |
| Spark Structured Streaming (`spark/streaming.py`) | ✅ Implementado |
| Docker Compose local (Kafka + Zookeeper + UI) | ✅ Implementado |
| Confluent Schema Registry (Avro) | 🟡 Roadmap futuro |
| Kafka no SquareCloud (prod) | 🟡 Requer Confluent Cloud ou Upstash |

---

## 8. Observabilidade e Gestão de Logs

### Dois sistemas de logging independentes

O projeto possui dois sistemas de logging com escopos diferentes:

| Sistema | Arquivo | Escopo | Formato |
|---------|---------|--------|---------|
| ETL | `utils/logger.py` | `PNCPExtractor`, `PNCPTransformer`, `MongoLoader`, `SQLiteLoader`, `ETLPipeline` | `timestamp \| LEVEL \| ClassName \| mensagem` |
| API + Spark | `api/main.py` (basicConfig) | `licitame`, `licitame.spark` | `timestamp [LEVEL] nome: mensagem` |

O nível de log do ETL é configurável via variável de ambiente `LOG_LEVEL` (padrão: `INFO`).

### Configuração API (`api/main.py`)

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
```

Todos os submódulos que instanciarem `logging.getLogger("licitame.*")` herdam automaticamente este handler.

### Eventos rastreados por componente

**ETL Pipeline:**

| Evento | Nível | Componente |
|--------|-------|-----------|
| Extrator inicializado | INFO | PNCPExtractor |
| Buscando página N de /contratos | DEBUG | PNCPExtractor |
| Página N — X registros (total: Y) | INFO | PNCPExtractor |
| Erro HTTP / conexão | ERROR | PNCPExtractor |
| X registros transformados | INFO | PNCPTransformer |
| Data inválida ignorada | WARNING | PNCPTransformer |
| Lote X/Y — N documentos upserted | INFO | MongoLoader |
| Erro no bulk_write | ERROR | MongoLoader |
| SQLite: N registros inseridos | INFO | SQLiteLoader |
| Pipeline ETL concluído em Xs | INFO | ETLPipeline |
| Erro crítico no pipeline | ERROR | ETLPipeline |

**API e Spark:**

| Evento | Nível | Logger |
|--------|-------|--------|
| LicitaME API iniciando | INFO | licitame |
| Conexão MongoDB estabelecida | INFO | licitame |
| API encerrada | INFO | licitame |
| PySpark iniciado (PID X) | INFO | licitame.spark |
| Pipeline concluído com sucesso | INFO | licitame.spark |
| Pipeline falhou (código + stderr) | ERROR | licitame.spark |
| Todas as requests HTTP | INFO | uvicorn.access (automático) |

### Exemplo de saída completa de uma run

```
2026-06-13 14:30:00 | INFO | ETLPipeline | === Pipeline ETL PNCP iniciado ===
2026-06-13 14:30:00 | INFO | PNCPExtractor | Extraindo contratos de 20260606 a 20260613
2026-06-13 14:30:01 | INFO | PNCPExtractor | Página 1 — 50 registros obtidos (total: 50)
2026-06-13 14:30:02 | INFO | PNCPExtractor | Total de contratos extraídos: 50
2026-06-13 14:30:02 | INFO | PNCPTransformer | 50 registros transformados com sucesso.
2026-06-13 14:30:02 | INFO | MongoLoader | Lote 1/1 — 50 documentos upserted.
2026-06-13 14:30:02 | INFO | SQLiteLoader | SQLite: 50 registros inseridos.
2026-06-13 14:30:02 | INFO | ETLPipeline | === Pipeline concluído em 2.14s | MongoDB: 50 | SQLite: 50 ===

2026-06-13 14:33:10 [INFO] licitame.spark: [SPARK] Pipeline iniciado em background (PID 4821).
2026-06-13 14:34:47 [INFO] licitame.spark: [SPARK] Pipeline concluído com sucesso (PID 4821).
```

---

## 9. MCP Server — Ferramentas como Protocolo

O **Model Context Protocol (MCP)** padroniza como modelos de linguagem consomem ferramentas externas. O projeto implementa o MCP em dois transports:

```
mcp_server/server.py    → MCP Protocol nativo (Claude Desktop, IDE plugins, VS Code)
api/mcp/router.py       → HTTP REST (qualquer cliente HTTP)
```

Ambos compartilham a mesma lógica em `api/mcp/service.py`, que delega execução para `api/analytics/service.py` — ou seja, todas as 4 ferramentas consultam o MongoDB diretamente.

### Endpoints REST

```
GET  /mcp/ferramentas
→ { "total": 4, "ferramentas": [...] }

POST /mcp/invocar
Body: { "nome": "top_orgaos", "argumentos": { "n": 3 } }
→ { "ferramenta": "top_orgaos", "resultado": "...", "sucesso": true }
```

### As 4 ferramentas

| Tool | Parâmetros | Fonte de dados | Retorno |
|------|-----------|---------------|---------|
| `buscar_contratos` | `palavra_chave` (required), `limite` (default 10) | MongoDB `find` com `$regex` case-insensitive em `objetoContrato` | Lista de contratos com numero_controle, objeto, valor, orgao |
| `estatisticas_contratos` | nenhum | MongoDB `$group` aggregation | total, média, max, min de `valorInicial` |
| `top_orgaos` | `n` (default 5) | MongoDB `groupBy + sort + limit` | Top N órgãos com total_contratos e valor_total |
| `contratos_favoraveis_mei` | `limite` (default 10) | MongoDB `find({valorInicial: {$lte: 80000}})` | Lista de contratos MEI com valor e órgão |

---

## 10. Chatbot Léo — Tool Calling com Claude

### Fluxo de execução

```
POST /chat/mensagem  { mensagem, historico[] }
         │
         ▼
  claude-sonnet-4-6
  system: [persona Léo — linguagem simples, foco MEI]
  tools: [buscar_contratos, estatisticas_contratos, top_orgaos, contratos_favoraveis_mei]
         │
         │  stop_reason = "tool_use"?
         ├────────────────────── SIM ────────────────────────┐
         │                                                   ▼
         │                                  _executar_tool(nome, args, db)
         │                                           │
         │                              ┌────────────┴───────────┐
         │                              ▼                        ▼
         │                       MongoDB find()         MongoDB aggregate()
         │                              │
         │                  resultado → tool_result → msgs
         │                              │
         │      ◄────── loop até end_turn ──────────────────────┘
         │
         │  stop_reason = "end_turn"
         ▼
  ChatResponse { resposta: string, ferramentas_usadas: string[] }
```

Claude pode encadear múltiplas tool calls na mesma interação antes de produzir a resposta final (ex: `estatisticas_contratos` → `buscar_contratos`).

### Quando cada tool é invocada

| Pergunta | Tool chamada |
|----------|-------------|
| "Tem edital de limpeza?" | `buscar_contratos("limpeza")` |
| "Quais órgãos publicam mais?" | `top_orgaos(n=5)` |
| "Quantos contratos tem na base?" | `estatisticas_contratos()` |
| "O que posso participar como MEI?" | `contratos_favoraveis_mei(limite=10)` |
| "Qual o valor médio dos contratos?" | `estatisticas_contratos()` |

### Persona do Léo (system prompt)

- Linguagem simples — MEI não é advogado
- Respostas curtas; sem introduções longas
- Valores sempre em R$ com separador de milhar
- Máximo 3 editais por resposta; oferecer continuar se houver mais
- Nunca inventa dados — se não encontrar, informa e sugere `pncp.gov.br`
- Não dá parecer jurídico — redireciona para contador/advogado
- Explica termos técnicos (CNAE, PNCP, CNPJ) na primeira ocorrência

---

## 11. Erros Mapeados e Resiliência da Pipeline

Nenhuma falha em um módulo derruba a API inteira. Cada camada tem isolamento de erro:

| Ponto de falha | Tratamento | Impacto |
|---------------|-----------|---------|
| API PNCP indisponível | Retry exponencial (3x, backoff 2–10s); se falhar, loga WARNING e retorna parcial | ETL parcial; Bronze não atualizado |
| MongoDB fora do ar (ETL) | `ConnectionFailure` levantada; pipeline logado e encerrado com ERROR | ETL falha; API continua servindo dados existentes |
| MongoDB fora do ar (API) | Motor retorna erro; FastAPI retorna 500 com mensagem humanizada | Endpoint específico falha; demais endpoints ok |
| PySpark sem dados | `if pdf.empty: spark.stop(); return` — sem CSV, sem write | Gold não atualizado; API retorna `disponivel: false` |
| CSVs Gold ausentes | `obter_dados_spark()` retorna `{ "disponivel": false }` | Dashboard sem dados Spark; Aggregation API ok |
| Tool do chatbot com erro | `_executar_tool` captura `Exception`; retorna string de erro para o Claude; Claude informa usuário | Resposta degradada sem expor traceback |
| Tool MCP inválida | `InvocarResponse(sucesso=False, resultado="Ferramenta X não existe")` | Resposta de erro controlada |
| `ANTHROPIC_API_KEY` ausente | `processar_mensagem` retorna `ChatResponse` com mensagem de config | Léo indisponível; demais rotas ok |
| Bulk write parcial no MongoDB | `BulkWriteError` logado com `exc.details`; exceção re-lançada | Batch parcial; próxima run re-tenta os mesmos registros (upsert) |
| `KAFKA_BOOTSTRAP_SERVERS` ausente | `_KAFKA_DISPONIVEL = False`; producer retorna 0; consumer retorna None | Kafka inativo; pipeline batch e API funcionam normalmente |
| `confluent-kafka` não instalado | `ImportError` capturado no import; fallback automático | Mesmo comportamento que variável ausente |
| Kafka broker indisponível (producer) | `_delivery_report` loga warning por mensagem não entregue | ETL continua; contratos gravados no MongoDB; Kafka sem mensagens |
| Kafka broker indisponível (consumer) | `KafkaError` logado; loop continua tentando | Silver/Gold streaming não atualizados; batch PySpark cobre na próxima run |
| Mensagem Kafka com JSON inválido | `json.JSONDecodeError` capturado; mensagem descartada com WARNING | Contrato ignorado no streaming; Bronze já contém o registro |
| upsert Silver/Gold falha (Motor) | `Exception` capturado em `_processar_contrato`; logado como ERROR | Contrato não refletido nas camadas streaming; batch corrige |

---

*LicitaME v1.0.0 · Engenharia de Dados · Junho 2026*
