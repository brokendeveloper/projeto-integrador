# Atividade ETL — Universidades do Mundo

## 👥 Integrantes do Grupo
- Luccas Fernandes

## 📋 Sobre o Projeto
Pipeline ETL em Python que extrai dados de universidades da API Hipolabs,
transforma e persiste em banco de dados SQLite para consultas futuras,
histórico e integração com outras aplicações.

## 🗄️ Modelagem do Banco de Dados

### Justificativa
Optou-se por normalizar o esquema em três tabelas para evitar redundância e
facilitar consultas analíticas. A tabela `universities` armazena os dados
escalares de cada instituição; `domains` e `web_pages` são tabelas satélite
com relação 1:N, pois uma universidade pode ter múltiplos domínios e URLs.
A constraint `UNIQUE(name, country)` impede duplicatas ao re-executar o pipeline.

### Diagrama / SQL de criação

```sql
CREATE TABLE IF NOT EXISTS universities (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    country         TEXT    NOT NULL,
    alpha_two_code  TEXT    NOT NULL,
    state_province  TEXT,
    UNIQUE(name, country)
);

CREATE TABLE IF NOT EXISTS domains (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    university_id   INTEGER NOT NULL,
    domain          TEXT    NOT NULL,
    FOREIGN KEY (university_id) REFERENCES universities(id)
);

CREATE TABLE IF NOT EXISTS web_pages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    university_id   INTEGER NOT NULL,
    url             TEXT    NOT NULL,
    FOREIGN KEY (university_id) REFERENCES universities(id)
);
```

## 🔄 Estratégia de Persistência Multi-País

### Estratégia escolhida
**INSERT OR IGNORE** com verificação via `cursor.rowcount`.

```python
cursor.execute("""
    INSERT OR IGNORE INTO universities
        (name, country, alpha_two_code, state_province)
    VALUES (?, ?, ?, ?)
""", (name, country, code, state))
```

### Justificativa
- **Consistência**: a constraint `UNIQUE(name, country)` no banco impede duplicatas
  em nível de banco de dados, independente da camada de aplicação.
- **Desempenho**: uma única instrução SQL por linha; o banco decide internamente
  se insere ou ignora, sem round-trips adicionais de `SELECT`.
- **Manutenibilidade**: lógica simples e declarativa — fácil de entender e testar.
- **Adequação ao domínio**: dados de universidades são históricos e raramente
  mudam; uma vez inseridos, o registro não precisa ser sobrescrito.

## ⚙️ Como Executar

### Pré-requisitos
- Python 3.12+
- pip

### Instalação
```bash
git clone https://github.com/brokendeveloper/atividade-etl.git
cd atividade-etl

python -m venv .venv

# Linux ou macOS
source .venv/bin/activate

# Windows (Command Prompt)
.venv\Scripts\activate

pip install -r requirements.txt
```

### Executar o pipeline ETL
```bash
python main.py
```

### Consultar dados gerados (exemplo)
```python
import sqlite3
import pandas as pd

connection = sqlite3.connect("db/universities.db")
df = pd.read_sql_query("SELECT * FROM universities LIMIT 10", connection)
print(df)
connection.close()
```

## 📦 Dependências
Veja `requirements.txt`. Principais:
- `requests` — chamadas HTTP à API
- `pandas` — manipulação e transformação de dados
- `black` — formatação padronizada do código
- `sqlite3` — nativo do Python (não precisa instalar)

## ⚠️ Observações
- A pasta `.venv/` **NÃO foi enviada** para o repositório (ver `.gitignore`)
- Código formatado com `black .` antes da entrega
- O arquivo `db/universities.db` é gerado localmente e **não está versionado**
