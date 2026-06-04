# LicitaME — Documentação Técnica

> Plataforma de apoio à participação de Microempreendedores Individuais (MEIs) em licitações públicas.
> Lei nº 14.133/2021 · LC 123/2006 · LGPD (Lei 13.709/2018)

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Stack Tecnológica e Justificativas](#3-stack-tecnológica-e-justificativas)
4. [Estrutura de Arquivos](#4-estrutura-de-arquivos)
5. [API REST — Módulos e Endpoints](#5-api-rest--módulos-e-endpoints)
6. [Autenticação e Segurança](#6-autenticação-e-segurança)
7. [App Mobile](#7-app-mobile)
8. [Pipeline ETL e Dados](#8-pipeline-etl-e-dados)
9. [Analytics e Chatbot](#9-analytics-e-chatbot)
10. [Testes](#10-testes)
11. [CI/CD](#11-cicd)
12. [LGPD e Conformidade](#12-lgpd-e-conformidade)
13. [Como Executar](#13-como-executar)
14. [Variáveis de Ambiente](#14-variáveis-de-ambiente)

---

## 1. Visão Geral

O LicitaME resolve um problema real: MEIs raramente participam de licitações públicas por desconhecimento do processo. A plataforma:

- **Busca editais** do PNCP (Portal Nacional de Contratações Públicas) em tempo real
- **Sinaliza** quais editais são favoráveis ao MEI (valor ≤ R$ 80.000 — LC 123/2006, Art. 48)
- **Gera checklist** automatizado de habilitação baseado na Lei 14.133/2021
- **Organiza documentos** de habilitação por edital (upload com GridFS)
- **Dispara alertas** quando novos editais correspondem ao perfil do MEI
- **Registra histórico** de participações e métricas de desempenho

---

## 2. Arquitetura do Sistema

```
┌──────────────────────────────────────────────────────────────────────┐
│                          CLIENTE MOBILE                              │
│                    Expo SDK 56 · React Native                        │
│         expo-router · axios · SecureStore · Ionicons                 │
└──────────────────────┬───────────────────────────────────────────────┘
                       │ HTTPS / JWT Bearer
┌──────────────────────▼───────────────────────────────────────────────┐
│                          API REST                                     │
│               FastAPI 0.115 · Python 3.12 · Uvicorn                  │
│   HTTPBearer · slowapi (rate limit) · SecurityHeaders · CORS         │
└──────────┬──────────────────────────────────────┬────────────────────┘
           │                                      │
┌──────────▼──────────┐               ┌───────────▼──────────────────┐
│      MongoDB Atlas  │               │  GridFS (documentos binários) │
│  Motor (async ODM)  │               │  motor.motor_asyncio          │
│  8 coleções         │               └──────────────────────────────┘
└──────────┬──────────┘
           │
┌──────────▼──────────────────────────────────────────────────────────┐
│                          PIPELINE ETL                                │
│            Python · requests · pandas · Motor · SQLite              │
│      PNCP API → extractor → transformer → loader → MongoDB          │
└─────────────────────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────────┐
│                       ANALYTICS / BI                                 │
│   PySpark (spark/) · Streamlit (dashboards/) · Claude API (chat/)   │
│   MCP Server (mcp_server/) · Tool Calling via claude-sonnet-4-6     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Stack Tecnológica e Justificativas

### Backend — FastAPI

**Por quê FastAPI e não Django REST / Flask?**

FastAPI foi escolhido por três razões objetivas para este projeto:
1. **Async nativo**: toda comunicação com MongoDB usa `motor` (asyncio), portanto o framework precisa suportar `async/await` sem adaptadores. Flask e Django REST exigem extensões externas.
2. **Documentação automática**: o Swagger/OpenAPI é gerado automaticamente a partir dos tipos Pydantic, sem escrever YAML. Para um projeto acadêmico, isso acelera muito a validação dos endpoints.
3. **Pydantic v2**: validação de entrada e saída com tipos Python nativos, sem decoradores extras.

### Banco de Dados — MongoDB Atlas + Motor

**Por quê MongoDB e não PostgreSQL?**

Os dados do PNCP chegam como JSON semi-estruturado (campos variam entre órgãos, alguns contratos têm `valorInicial`, outros `valor_inicial`). Um schema relacional exigiria mapeamento e normalização de cada variante. O MongoDB permite armazenar os documentos PNCP diretamente, com o `_serializar_edital()` fazendo a normalização na leitura.

O **Motor** (motor.motor_asyncio) é o driver oficial async para MongoDB, compatível com o event loop do FastAPI.

### Autenticação — JWT com HTTPBearer

**Por quê JWT e não sessions?**

O app mobile não tem estado de servidor — cada requisição carrega o token no header `Authorization: Bearer <token>`. Sessions exigiriam armazenamento no servidor e cookies, incompatíveis com mobile nativo. O JWT é verificado em cada request via `get_usuario_atual()` em `api/dependencies.py`, sem consulta ao banco.

**HTTPBearer vs OAuth2PasswordBearer**: HTTPBearer foi escolhido para retornar 403 (proibido) ao invés de 401 com `WWW-Authenticate: Bearer`, evitando pop-ups de autenticação básica em ferramentas como Postman.

### App Mobile — Expo SDK 56 + expo-router

**Por quê Expo e não React Native CLI?**

Expo elimina a necessidade de configurar Xcode/Android Studio para desenvolvimento. O SDK 56 com `expo-router` traz file-based routing (igual ao Next.js), tornando a navegação declarativa — adicionar uma tela é criar um arquivo `.tsx` na pasta `app/`.

**Por quê expo-router e não React Navigation?**

expo-router usa o mesmo paradigma de diretórios que Next.js. Grupos como `(auth)` e `(tabs)` controlam o layout sem afetar a URL. Deeplinks e parâmetros de rota (`useLocalSearchParams`) funcionam de forma nativa.

### Gerenciamento de Estado Auth — React Context

**Por quê Context API e não Zustand/Redux?**

O problema específico era: múltiplos componentes precisavam compartilhar `autenticado: boolean`. Zustand ou Redux seriam over-engineering para um estado tão simples. O Context API resolve exatamente isso: um `AuthProvider` envolve toda a árvore, e `useAuth()` lê o mesmo estado em qualquer componente.

O ponto crítico: a interceptação de erros 401 (token expirado) precisa chamar `setAutenticado(false)`. Isso só é possível dentro do `AuthProvider`, onde o setter está em escopo. Por isso o interceptor Axios foi movido de `api.ts` para dentro do `useEffect` do `AuthContext.tsx`.

### Configurações com Toggle (Switch)

**Por quê Switch e não botões de opção?**

Preferências binárias (ativar/desativar notificação) têm estado natural de liga/desliga. O componente `Switch` do React Native comunica isso visualmente com uma animação deslizante familiar ao usuário móvel. Botões exigiriam dois estados explícitos ("ativar" / "desativar") e mais área de toque.

O padrão de **atualização otimista** foi usado: o toggle muda imediatamente na UI, a requisição PATCH vai para o servidor em background, e em caso de erro o valor anterior é restaurado (`setConfig((prev) => ({ ...prev, [chave]: anterior }))`). Isso elimina latência percebida.

### Side Menu — Modal com Animated

**Por quê Modal e não View absolutePositioned?**

O `Modal` com `transparent={true}` garante que o drawer apareça acima de tudo, incluindo o Tab Bar nativo do `expo-router`. Uma `View` com `position: absolute` ficaria abaixo do Tab Bar em iOS/Android porque o Tab Bar é renderizado em uma camada nativa separada.

O `Animated.spring` com `tension: 70` e `friction: 11` imita a física de um drawer real — decelera naturalmente ao final do movimento sem ultrapassar a posição alvo.

### PySpark

**Por quê PySpark e não pandas puro?**

O PNCP pode conter dezenas de milhares de contratos. PySpark foi incluído para demonstrar processamento distribuído — o pipeline em `spark/pyspark_transform.py` lê do MongoDB, aplica 4 transformações (filtragem MEI, agregação por UF, ranking de órgãos, análise temporal) e exporta CSVs. Academicamente, demonstra o componente de Engenharia de Dados do projeto.

### Chatbot Léo — Claude API com Tool Calling

**Por quê tool calling e não apenas RAG?**

Tool calling permite que o modelo decida *quando* consultar os dados e *qual* ferramenta usar. Com RAG puro, o contexto seria injetado na prompt sem controle do modelo. Com tool calling, o modelo (claude-sonnet-4-6) chama `buscar_contratos`, `estatisticas`, `top_orgaos` ou `contratos_mei` conforme a intenção do usuário, retornando dados atualizados do MongoDB em tempo real.

---

## 4. Estrutura de Arquivos

```
projeto-integrador/
│
├── api/                          # Backend FastAPI
│   ├── main.py                   # App principal, registra todos os routers
│   ├── dependencies.py           # get_db, get_usuario_atual (injeção)
│   ├── middleware.py             # slowapi (rate limit) + SecurityHeaders
│   ├── auth/                     # Registro, login, JWT
│   ├── editais/                  # Busca PNCP com filtros e paginação
│   ├── checklist/                # Checklist Lei 14.133 + progresso por usuário
│   ├── documentos/               # Upload/download via GridFS
│   ├── alertas/                  # CRUD de alertas com limite por plano
│   ├── historico/                # Registro e métricas de participações
│   ├── perfil/                   # Edição de nome, e-mail, CNPJ, senha
│   ├── config/                   # Preferências de notificações e filtros
│   ├── plano/                    # Gerenciamento de plano free/premium
│   ├── analytics/                # Endpoints de BI (top órgãos, estatísticas)
│   ├── chat/                     # Chatbot Léo com Claude + tool calling
│   ├── mcp/                      # Servidor MCP (tools expostos via HTTP)
│   └── lgpd/                     # Exportar dados, excluir conta (LGPD)
│
├── etl/                          # Pipeline de dados PNCP
│   ├── extractor.py              # Consume API PNCP com paginação e retry
│   ├── transformer.py            # Normaliza datas, valores, remove nulos
│   ├── loader.py                 # Upsert no MongoDB Atlas + SQLite local
│   └── pipeline.py               # Orquestra o ETL completo
│
├── spark/
│   └── pyspark_transform.py      # 4 transformações PySpark sobre contratos
│
├── mcp_server/
│   └── server.py                 # MCP server com 4 tools (buscar, stats, etc.)
│
├── dashboards/
│   ├── dashboard.py              # Dashboard Streamlit + Plotly
│   └── chatbot.py                # Chatbot Streamlit com Claude
│
├── mobile/                       # App Expo SDK 56
│   ├── app/
│   │   ├── _layout.tsx           # Stack root com AuthProvider + 4 telas extras
│   │   ├── (auth)/               # login.tsx, register.tsx
│   │   ├── (tabs)/               # 5 abas principais do MVP
│   │   │   ├── index.tsx         # RF01 — Lista e busca de editais
│   │   │   ├── checklist.tsx     # RF02 — Checklist de habilitação
│   │   │   ├── documentos.tsx    # RF03 — Upload de documentos
│   │   │   ├── alertas.tsx       # RF04 — Criação e gerenciamento de alertas
│   │   │   └── historico.tsx     # RF05 — Histórico de participações
│   │   ├── perfil.tsx            # Edição de perfil
│   │   ├── configuracoes.tsx     # Toggle de notificações e filtros
│   │   ├── premium.tsx           # Plano free vs premium
│   │   └── ajuda.tsx             # FAQ + base legal + contato
│   ├── components/
│   │   └── SideMenu.tsx          # Drawer animado com Modal
│   ├── context/
│   │   └── AuthContext.tsx       # Estado de autenticação compartilhado
│   ├── hooks/
│   │   └── useAuth.ts            # Re-exporta useAuth do AuthContext
│   ├── services/
│   │   └── api.ts                # Axios configurado com token SecureStore
│   └── constants/
│       └── theme.ts              # Design tokens: Colors, Spacing, Radius, Shadow
│
├── tests/
│   ├── test_extractor.py         # ETL: extração do PNCP
│   ├── test_transformer.py       # ETL: normalização de dados
│   ├── test_loader.py            # ETL: persistência no MongoDB
│   ├── test_auth.py              # API: registro, login, duplicados
│   ├── test_editais.py           # API: busca, paginação, favoravel_mei
│   ├── test_checklist.py         # API: checklist, progresso, planos
│   ├── test_alertas.py           # API: criação, limite free, listagem
│   └── test_historico.py         # API: participações, métricas
│
├── .github/workflows/
│   └── ci.yml                    # GitHub Actions: pytest no push
│
└── docs/
    ├── analise-seguranca.md      # Análise de segurança e OWASP
    ├── modelo-negocio.md         # Canvas de modelo de negócio
    └── arquitetura-tecnica.md    # Este documento
```

---

## 5. API REST — Módulos e Endpoints

| Módulo | Prefixo | Endpoints principais |
|--------|---------|---------------------|
| auth | `/auth` | `POST /register`, `POST /login` |
| editais | `/editais` | `GET /editais`, `GET /editais/{id}` |
| checklist | `/editais/{id}/checklist` | `GET`, `PATCH` |
| documentos | `/documentos` | `POST /upload`, `GET /listar`, `GET /{id}`, `DELETE /{id}` |
| alertas | `/alertas` | `POST`, `GET`, `DELETE /{id}` |
| historico | `/historico` | `POST`, `GET`, `GET /resumo` |
| perfil | `/perfil` | `GET`, `PATCH` |
| config | `/config` | `GET`, `PATCH` |
| plano | `/plano` | `GET`, `POST /upgrade` |
| analytics | `/analytics` | `GET /estatisticas`, `GET /top-orgaos`, `GET /contratos-mei`, `POST /executar-spark` |
| chat | `/chat` | `POST /mensagem` |
| mcp | `/mcp` | `GET /ferramentas`, `POST /invocar` |
| lgpd | `/lgpd` | `GET /meus-dados`, `DELETE /minha-conta` |

**Swagger UI**: `http://localhost:8000/docs`
**ReDoc**: `http://localhost:8000/redoc`

### Fluxo central de uma requisição autenticada

```
Request → CORS Middleware → SecurityHeaders Middleware
       → slowapi RateLimiter (10 req/min em /auth/*)
       → FastAPI Router
       → Depends(get_usuario_atual)  ← verifica JWT, busca usuário no MongoDB
       → Handler → Service → MongoDB
       → Pydantic Response Validation
       → JSON Response
```

---

## 6. Autenticação e Segurança

### Registro e Login

```
POST /auth/register { nome, email, cnpj, senha }
→ valida unicidade de email e CNPJ
→ bcrypt.hash(senha, rounds=12)
→ insere no MongoDB
→ retorna { access_token, token_type: "bearer" }

POST /auth/login { email, senha }
→ busca usuário por email
→ bcrypt.verify(senha, hash)
→ gera JWT com { sub: str(user_id), exp: now + JWT_EXPIRE_MINUTES }
→ retorna { access_token, token_type: "bearer" }
```

### Proteção dos endpoints

Todos os endpoints (exceto `/auth/*`, `/health`, `/docs`, `/redoc`) exigem `Authorization: Bearer <token>`. A dependência `get_usuario_atual` em `api/dependencies.py`:
1. Extrai o token do header
2. Verifica assinatura HMAC-SHA256 com `JWT_SECRET_KEY`
3. Busca o usuário no MongoDB por `_id`
4. Retorna o documento do usuário (disponível nos handlers como `usuario: dict`)

### Rate Limiting

`slowapi` limita `/auth/login` e `/auth/register` a **10 requisições/minuto por IP**. Excedendo o limite: HTTP 429 com `Retry-After` no header.

### Security Headers

`SecurityHeadersMiddleware` injeta em todas as respostas:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

---

## 7. App Mobile

### Navegação

```
RootLayout (AuthProvider)
└── Stack
    ├── (auth) — sem header
    │   ├── login.tsx
    │   └── register.tsx
    ├── (tabs) — header dark + hamburger
    │   ├── index.tsx        (Editais)
    │   ├── checklist.tsx    (Checklist)
    │   ├── documentos.tsx   (Documentos)
    │   ├── alertas.tsx      (Alertas)
    │   └── historico.tsx    (Histórico)
    ├── perfil.tsx           (header: "Editar Perfil")
    ├── configuracoes.tsx    (header: "Configurações")
    ├── premium.tsx          (header: "Plano Premium")
    └── ajuda.tsx            (header: "Ajuda & Suporte")
```

### Fluxo de autenticação

```
App abre → AuthProvider lê token do SecureStore
         → autenticado = null (carregando)
         → autenticado = true  → redireciona para /(tabs)
         → autenticado = false → redireciona para /(auth)/login

Login bem-sucedido → salva token no SecureStore → setAutenticado(true) → tabs
Token expirado (401) → interceptor Axios → removerToken → setAutenticado(false) → login
Logout → removerToken → setAutenticado(false) → login
```

### Design System

Todos os estilos usam tokens de `mobile/constants/theme.ts`:

| Token | Uso |
|-------|-----|
| `Colors.primary` | `#2563EB` — azul principal (botões, links, ícones ativos) |
| `Colors.primaryDark` | `#1E3A8A` — headers, hero do login |
| `Colors.success` | `#059669` — editais favoráveis ao MEI, borda verde |
| `Colors.premium` | `#7C3AED` — itens premium, plano pago |
| `Colors.danger` | `#DC2626` — botão sair, erros |
| `Spacing.*` | xs=4, sm=8, md=16, lg=20, xl=24, xxl=32 |
| `Radius.*` | sm=8, md=12, lg=16 |
| `Shadow.*` | sm/md — sombras com elevation para Android |

### Navegação edital → checklist

Ao tocar em um card de edital, `router.push({ pathname: "/(tabs)/checklist", params: { editalId: item.id } })` navega para a aba de checklist. O `checklist.tsx` lê o parâmetro com `useLocalSearchParams` e, ao ganhar foco (`useFocusEffect`), preenche o campo e carrega automaticamente o checklist via `GET /editais/{editalId}/checklist`.

---

## 8. Pipeline ETL e Dados

### Extração

`etl/extractor.py` consome a API pública do PNCP (`https://pncp.gov.br/api/consulta/v1/contratos`) com:
- Paginação automática (parâmetro `pagina`)
- Retry exponencial em falhas de rede (até 3 tentativas)
- Filtro por data de publicação

### Transformação

`etl/transformer.py` normaliza:
- Datas para ISO 8601
- Valores monetários para `float`
- Remove documentos com campos obrigatórios nulos
- Padroniza nomenclatura de campos (`valorInicial` → aceito como-é, sem renomear para manter compatibilidade)

### Carga

`etl/loader.py` faz **upsert** no MongoDB usando `numeroControlePNCP` como chave única. Também persiste em SQLite local para auditoria offline.

### Dados Atuais

801 contratos do PNCP carregados na coleção `contratos` do MongoDB. Os dados são estáticos para o MVP — em produção, o ETL rodaria em cron diário.

---

## 9. Analytics e Chatbot

### PySpark (`spark/pyspark_transform.py`)

4 transformações sobre a coleção `contratos`:
1. **Filtragem MEI**: contratos com `valorInicial ≤ 80000`
2. **Ranking por UF**: contagem e soma de valores por estado
3. **Top órgãos**: órgãos com mais contratos
4. **Série temporal**: distribuição por mês de publicação

Execução via `POST /analytics/executar-spark` (endpoint autenticado).

### Chatbot Léo (`api/chat/router.py` + `dashboards/chatbot.py`)

Implementado com **tool calling** da Claude API (modelo `claude-sonnet-4-6`). O modelo decide qual ferramenta chamar:

| Tool | O que faz |
|------|-----------|
| `buscar_contratos` | Busca no MongoDB com filtros opcionais |
| `estatisticas` | Retorna métricas gerais (total, MEI, valor médio) |
| `top_orgaos` | Top N órgãos por volume de contratos |
| `contratos_mei` | Contratos com valor ≤ 80.000 |

O Streamlit em `dashboards/chatbot.py` oferece interface visual para o chatbot.

---

## 10. Testes

```
tests/
├── test_extractor.py    — Mock da API PNCP, verifica paginação e retry
├── test_transformer.py  — Normalização de datas e valores
├── test_loader.py       — Upsert no MongoDB mockado
├── test_auth.py         — Registro, login, e-mail duplicado, credenciais inválidas
├── test_editais.py      — Paginação, favoravel_mei, busca por ID, proteção auth
├── test_checklist.py    — Estrutura, progresso, diferença free/premium, toggle item
├── test_alertas.py      — Criar alerta, limite free (3), listagem
└── test_historico.py    — Registrar participação, listar, resumo de métricas
```

**Total: 33 testes — todos passando.**

Padrão usado: `pytest-asyncio` + `httpx.AsyncClient(ASGITransport)` + mocks em memória do MongoDB (`MagicMock` + funções async). A dependência `get_usuario_atual` é substituída via `app.dependency_overrides` para isolar a lógica de negócio.

Executar:
```bash
python3 -m pytest tests/ -v
```

---

## 11. CI/CD

`.github/workflows/ci.yml` roda em cada `push` e `pull_request`:

```yaml
steps:
  - Checkout do código
  - Setup Python 3.12
  - pip install -r requirements.txt
  - pytest tests/ -v
```

Variáveis de ambiente de teste são configuradas como GitHub Secrets: `JWT_SECRET_KEY`, `MONGODB_URI` (Atlas de testes), `ANTHROPIC_API_KEY`.

---

## 12. LGPD e Conformidade

A Lei 13.709/2018 (LGPD) é atendida por:

| Direito LGPD | Implementação |
|-------------|---------------|
| Acesso aos dados | `GET /lgpd/meus-dados` — retorna todos os dados do usuário em JSON |
| Exclusão | `DELETE /lgpd/minha-conta` — remove usuário, alertas, histórico, documentos e checklist |
| Criptografia | Senhas com `bcrypt` (rounds=12), nunca armazenadas em texto plano |
| Minimização | Apenas dados necessários coletados: nome, e-mail, CNPJ |

---

## 13. Como Executar

### Backend

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com MONGODB_URI, JWT_SECRET_KEY, ANTHROPIC_API_KEY

# Rodar a API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Documentação interativa
open http://localhost:8000/docs
```

### ETL (popular o banco)

```bash
python3 main.py
```

### App Mobile

```bash
cd mobile
npm install
npx expo start
# Escanear QR code com Expo Go (iOS/Android)
```

### Dashboard / Chatbot

```bash
streamlit run dashboards/dashboard.py
streamlit run dashboards/chatbot.py
```

### Testes

```bash
python3 -m pytest tests/ -v
```

---

## 14. Variáveis de Ambiente

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `MONGODB_URI` | URI de conexão MongoDB Atlas | `mongodb+srv://user:pass@cluster.mongodb.net` |
| `MONGODB_DB` | Nome do banco de dados | `licitame` |
| `JWT_SECRET_KEY` | Chave HMAC para assinar tokens | string aleatória longa |
| `JWT_ALGORITHM` | Algoritmo JWT | `HS256` |
| `JWT_EXPIRE_MINUTES` | Expiração do token | `1440` (24h) |
| `ANTHROPIC_API_KEY` | Chave da Claude API (chatbot Léo) | `sk-ant-...` |
| `EXPO_PUBLIC_API_URL` | URL da API para o app mobile | `http://192.168.1.x:8000` |

---

*Documentação gerada em: junho de 2025 · LicitaME v1.0.0*
