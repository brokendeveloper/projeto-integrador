# LicitaME

**Plataforma de Apoio à Concorrência Pública para Microempreendedores Individuais**

> Democratizando o acesso às licitações públicas para os mais de 15 milhões de MEIs brasileiros, com base na Lei 14.133/2021 e na LC 123/2006.

---

## O Problema

MEIs têm direito a tratamento preferencial em licitações de até R$ 80.000 — mas 92% nunca participaram de uma. Os principais obstáculos são burocracia documental, dificuldade de monitorar editais e complexidade legal. A LicitaME resolve isso com um app mobile simples, um checklist automatizado e alertas inteligentes.

---

## Arquitetura da Solução

```
┌────────────────────────────────────────────────────────────────┐
│                        FONTES DE DADOS                         │
│                                                                 │
│   API PNCP (pncp.gov.br)  ──────────►  ETL Pipeline           │
│                                          │                     │
│                                          ▼                     │
│                                     MongoDB Atlas              │
│                                     (coleção: contratos)       │
└────────────────────────────────────────┬───────────────────────┘
                                         │
                    ┌────────────────────▼───────────────────┐
                    │              API REST (FastAPI)         │
                    │                                         │
                    │  /auth      → JWT + bcrypt             │
                    │  /editais   → busca com filtros        │
                    │  /checklist → Lei 14.133/2021          │
                    │  /documentos→ upload GridFS            │
                    │  /alertas   → notificações MEI         │
                    │  /historico → participações            │
                    │  /analytics → métricas agregadas       │
                    │  /chat      → chatbot Léo (Claude AI)  │
                    │  /lgpd      → direitos LGPD            │
                    └────────────────────┬───────────────────┘
                                         │
                    ┌────────────────────▼───────────────────┐
                    │         App Mobile (Expo + RN)          │
                    │                                         │
                    │  Login / Registro                       │
                    │  RF01 — Busca de editais               │
                    │  RF02 — Checklist de habilitação       │
                    │  RF03 — Upload de documentos           │
                    │  RF04 — Alertas de prazos              │
                    │  RF05 — Histórico de participações     │
                    └────────────────────────────────────────┘

Componentes adicionais:
  dashboards/        → Streamlit + Plotly (análise exploratória)
  spark/             → PySpark (transformações em lote)
  mcp_server/        → Servidor MCP (tool calling)
  dashboards/chatbot → Chatbot Léo com Claude AI
```

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| ETL | Python 3.12, requests, tenacity, pymongo |
| API | FastAPI, Motor (async MongoDB), python-jose, passlib |
| Banco | MongoDB Atlas, SQLite (backup local) |
| Mobile | Expo SDK 56, React Native, TypeScript, expo-router |
| IA | Claude (Anthropic) via tool calling |
| Big Data | PySpark, Spark SQL |
| DevOps | GitHub Actions CI, pytest |
| Dashboards | Streamlit, Plotly |

---

## Pré-requisitos

- Python 3.12+
- Node.js 18+ e npm
- Conta MongoDB Atlas (ou MongoDB local)
- Expo Go no celular (para testar o app) ou emulador Android/iOS

---

## Setup do Backend

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd projeto-integrador

# 2. Crie o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais
```

### Variáveis de ambiente necessárias

```env
# MongoDB
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/pncp
MONGODB_DB_NAME=pncp

# JWT
JWT_SECRET_KEY=gere-uma-string-longa-e-aleatoria-aqui
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# API
API_HOST=0.0.0.0
API_PORT=8000
API_ENV=development

# Claude AI (para chatbot Léo)
ANTHROPIC_API_KEY=sk-ant-...
```

### Executar a API

```bash
uvicorn api.main:app --reload
# API disponível em http://localhost:8000
# Documentação Swagger em http://localhost:8000/docs
```

### Executar o ETL

```bash
python main.py
# Busca dados do PNCP e persiste no MongoDB
```

### Executar o dashboard Streamlit

```bash
streamlit run dashboards/dashboard.py
```

---

## Setup do App Mobile

```bash
cd mobile

# Instalar dependências
npm install

# Configurar variável de ambiente
echo "EXPO_PUBLIC_API_URL=http://SEU_IP_LOCAL:8000" > .env

# Iniciar o servidor de desenvolvimento
npx expo start
```

Aponte o Expo Go para o QR code exibido no terminal.

> **Importante**: substitua `SEU_IP_LOCAL` pelo IP da sua máquina na rede local (ex: `192.168.0.10`). `localhost` não funciona no dispositivo físico.

---

## Como Rodar os Testes

```bash
# Testes da API (módulos auth, alertas, histórico, ETL)
pytest tests/ -v

# Filtrar apenas testes da API
pytest tests/test_auth.py tests/test_alertas.py tests/test_historico.py -v
```

---

## Endpoints da API

Documentação interativa completa disponível em `/docs` (Swagger UI).

### Autenticação

| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| `POST` | `/auth/register` | Registrar novo MEI | Não |
| `POST` | `/auth/login` | Login e obtenção de token JWT | Não |

### Editais (RF01)

| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| `GET` | `/editais` | Listar editais com filtros (busca, CNAE, valor, região) | Sim |
| `GET` | `/editais/{id}` | Detalhes de um edital | Sim |

### Checklist (RF02)

| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| `GET` | `/editais/{id}/checklist` | Checklist de habilitação Lei 14.133/2021 | Sim |
| `PATCH` | `/editais/{id}/checklist` | Marcar item do checklist como concluído | Sim |

### Documentos (RF03)

| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| `POST` | `/editais/{id}/documentos` | Upload de documento (PDF, Word, JPG, PNG — máx 10 MB) | Sim |
| `GET` | `/editais/{id}/documentos` | Listar documentos enviados para o edital | Sim |
| `DELETE` | `/editais/{id}/documentos/{doc_id}` | Remover documento | Sim |

### Alertas (RF04)

| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| `POST` | `/alertas` | Criar alerta de edital (limite: 3 no plano free) | Sim |
| `GET` | `/alertas` | Listar alertas do usuário | Sim |
| `DELETE` | `/alertas/{id}` | Remover alerta | Sim |

### Histórico (RF05)

| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| `POST` | `/historico` | Registrar participação em edital | Sim |
| `GET` | `/historico` | Listar participações | Sim |
| `GET` | `/historico/resumo` | Métricas: total, vencidas, perdidas, em andamento | Sim |

### Analytics

| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| `GET` | `/analytics/estatisticas` | Estatísticas gerais dos contratos | Sim |
| `GET` | `/analytics/top-orgaos` | Órgãos que mais publicam contratos | Sim |
| `GET` | `/analytics/contratos-mei` | Contratos favoráveis a MEI (≤ R$ 80k) | Sim |

### Chatbot Léo (IA)

| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| `POST` | `/chat/mensagem` | Enviar mensagem ao chatbot Léo (Claude AI) | Sim |

### LGPD

| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| `GET` | `/lgpd/meus-dados` | Exportar todos os dados do usuário | Sim |
| `DELETE` | `/lgpd/minha-conta` | Excluir conta e todos os dados permanentemente | Sim |

### Sistema

| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| `GET` | `/health` | Health check da API | Não |

---

## Estrutura do Projeto

```
projeto-integrador/
│
├── api/                        # API REST (FastAPI)
│   ├── main.py                 # App principal + routers
│   ├── dependencies.py         # Injeção de dependências
│   ├── middleware.py           # Rate limiting + headers de segurança
│   ├── auth/                   # JWT, bcrypt, registro/login
│   ├── editais/                # RF01 — Busca de editais
│   ├── checklist/              # RF02 — Checklist Lei 14.133/2021
│   ├── documentos/             # RF03 — Upload GridFS
│   ├── alertas/                # RF04 — Alertas de editais
│   ├── historico/              # RF05 — Histórico de participações
│   ├── analytics/              # Métricas agregadas
│   ├── chat/                   # Chatbot Léo (Claude AI)
│   ├── mcp/                    # Servidor MCP
│   └── lgpd/                   # Direitos LGPD
│
├── mobile/                     # App Expo SDK 56 + TypeScript
│   ├── app/
│   │   ├── (auth)/             # login.tsx, register.tsx
│   │   ├── (tabs)/             # 5 telas MVP
│   │   └── _layout.tsx
│   ├── services/api.ts         # Axios + interceptors JWT
│   ├── hooks/useAuth.ts        # Hook de autenticação
│   └── constants/theme.ts
│
├── etl/                        # Pipeline ETL PNCP → MongoDB
│   ├── extractor.py            # Consumo da API PNCP
│   ├── transformer.py          # Normalização de dados
│   ├── loader.py               # Upsert MongoDB + SQLite
│   └── pipeline.py             # Orquestração
│
├── spark/                      # Transformações PySpark
├── mcp_server/                 # Servidor MCP (tool calling)
├── dashboards/                 # Streamlit + chatbot
├── docs/                       # Documentação do projeto
│   ├── analise-seguranca.md    # Análise de segurança e LGPD
│   └── modelo-negocio.md       # Modelo freemium e métricas
│
├── tests/                      # Testes pytest
├── config/settings.py          # Configurações via .env
├── utils/logger.py             # Logger centralizado
├── .env.example                # Template de variáveis de ambiente
├── requirements.txt            # Dependências Python
└── .github/workflows/ci.yml    # GitHub Actions CI
```

---

## Requisitos Funcionais

| Requisito | Descrição | Status |
|---|---|---|
| RF01 | Busca e filtro de editais por CNAE, valor e região | Implementado |
| RF02 | Checklist automatizado de requisitos (Lei 14.133/2021) | Implementado |
| RF03 | Upload e organização de documentos para habilitação | Implementado |
| RF04 | Alertas e notificações de prazos para MEIs | Implementado |
| RF05 | Dashboard de histórico de participações | Implementado |

---

## Segurança

- Autenticação JWT com expiração configurável
- Senhas protegidas com bcrypt (passlib)
- Rate limiting em endpoints de autenticação (10 req/min)
- Headers HTTP de segurança (HSTS, X-Frame-Options, CSP)
- Upload com whitelist de tipos MIME e limite de 10 MB
- Hash SHA-256 de documentos armazenados
- Endpoints LGPD para exportação e exclusão de dados
- Detalhes: [`docs/analise-seguranca.md`](docs/analise-seguranca.md)

---

## Modelo de Negócio

Modelo freemium com plano gratuito (até 3 alertas) e plano premium (alertas ilimitados + funcionalidades avançadas).

Detalhes: [`docs/modelo-negocio.md`](docs/modelo-negocio.md)

---

## Participantes

- **Luccas Fernandes**
- **Gabriel Nogueira**
- **Maria Eduarda Pernambuco**
- **Luiz Henrique Cavalcanti**
- **Nathalia Carvalho**
- **Carlos Cavalcante**

---

## Licença

Projeto acadêmico — uso educacional.
