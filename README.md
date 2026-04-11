# ETL PNCP — Pipeline de Dados de Contratações Públicas

## Descrição

Pipeline ETL em Python que consome dados da API pública do **PNCP (Portal Nacional de Contratações Públicas)**, realiza limpeza e normalização dos dados e os persiste no **MongoDB Atlas**. O projeto segue os princípios de Engenharia de Dados: orientação a objetos, responsabilidade única por módulo, logging centralizado e configurações via variáveis de ambiente.

## Arquitetura da Solução

```
API PNCP
   │
   ▼
PNCPExtractor  ──────► PNCPTransformer  ──────► MongoLoader  ──► MongoDB Atlas
(etl/extractor.py)     (etl/transformer.py)     (etl/loader.py)
                                         │
                                         └───► SQLiteLoader  ──► db/contratos.db
                                               (diferencial)
   │
   └── ETLPipeline (etl/pipeline.py) orquestra tudo
```

## Fluxo de Dados

1. **Extração**: `PNCPExtractor` realiza chamadas paginadas aos endpoints `/contratos` e `/atas` da API do PNCP, com retry automático usando backoff exponencial (`tenacity`).
2. **Transformação**: `PNCPTransformer` normaliza datas para ISO 8601, converte valores monetários para `float`, remove campos nulos e adiciona metadados `_etl_timestamp` e `_source`.
3. **Carga**: `MongoLoader` realiza upsert em lotes no MongoDB Atlas usando `numeroControlePNCP` como chave única. `SQLiteLoader` persiste os dados localmente como diferencial.

## Tecnologias Utilizadas

- Python 3.12+
- `pymongo` — cliente MongoDB Atlas
- `requests` — chamadas HTTP à API do PNCP
- `tenacity` — retry com backoff exponencial
- `python-dotenv` — carregamento de variáveis de ambiente
- `pandas` + `pyarrow` — manipulação de dados e suporte a Parquet
- `streamlit` + `plotly` — dashboard interativo (diferencial)
- `pytest` — testes unitários

## Configuração do Ambiente

```bash
git clone <url-do-repositorio>
cd etl-project

python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt

cp .env.example .env
# Edite .env com suas credenciais do MongoDB Atlas
```

## Como Executar

```bash
python main.py
```

Para executar o dashboard:
```bash
streamlit run dashboards/dashboard.py
```

Para rodar os testes:
```bash
pytest tests/ -v
```

## Estrutura do Projeto

```
/
├── etl/
│   ├── __init__.py
│   ├── extractor.py        # PNCPExtractor — chamadas à API do PNCP
│   ├── transformer.py      # PNCPTransformer — limpeza e normalização
│   ├── loader.py           # MongoLoader + SQLiteLoader — persistência
│   └── pipeline.py         # ETLPipeline — orquestração
├── config/
│   └── settings.py         # Configurações via variáveis de ambiente
├── utils/
│   └── logger.py           # Logger centralizado
├── tests/
│   ├── test_extractor.py
│   ├── test_transformer.py
│   └── test_loader.py
├── notebooks/
│   └── exploratory_analysis.ipynb  # EDA dos dados coletados
├── dashboards/
│   └── dashboard.py        # Dashboard Streamlit (diferencial)
├── db/                     # Banco SQLite local (gerado em runtime)
├── .env.example            # Template de variáveis de ambiente
├── requirements.txt
├── README.md
└── main.py                 # Ponto de entrada
```

## Coleções no MongoDB

Coleção `contratos` — campos principais:

| Campo | Tipo | Descrição |
|---|---|---|
| `numeroControlePNCP` | string | Identificador único do contrato (chave de upsert) |
| `orgaoEntidade` | object | Dados do órgão (CNPJ, razão social) |
| `dataPublicacaoPncp` | string ISO 8601 | Data de publicação no PNCP |
| `dataVigenciaInicio` | string ISO 8601 | Início da vigência |
| `dataVigenciaFim` | string ISO 8601 | Fim da vigência |
| `valorInicial` | float | Valor inicial do contrato em R$ |
| `objetoContrato` | string | Descrição do objeto contratado |
| `_etl_timestamp` | string ISO 8601 | Timestamp da execução do pipeline |
| `_source` | string | Sempre `"pncp_api"` |

## Dificuldades e Decisões de Projeto

- **Paginação heterogênea**: A API do PNCP pode retornar lista direta ou objeto com campo `data`. O extrator trata ambos os formatos.
- **Upsert vs insert**: Optou-se por upsert usando `numeroControlePNCP` para garantir idempotência — o pipeline pode ser reexecutado sem gerar duplicatas.
- **Retry com backoff**: `tenacity` foi escolhido pela legibilidade dos decorators e configuração declarativa de estratégia de retry.
- **Persistência dupla**: MongoDB Atlas como banco principal (NoSQL, flexível para dados semi-estruturados da API) e SQLite como backup local para análises offline.

## Diferenciais Implementados

- **SQLiteLoader**: persistência adicional local em `db/contratos.db`
- **Dashboard Streamlit**: visualização interativa em `dashboards/dashboard.py`
- **Notebook EDA**: análise exploratória em `notebooks/exploratory_analysis.ipynb`
- **Retry automático**: backoff exponencial com `tenacity` (3 tentativas)
- **Rate limiting**: `time.sleep(0.5)` entre páginas para respeitar limites da API
