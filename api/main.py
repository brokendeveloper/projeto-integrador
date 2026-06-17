import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient

from config.settings import MONGODB_DB, MONGODB_URI

# Configuração centralizada de logging — todas as submódulos herdam este handler
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("licitame")
from api.auth.router import router as auth_router
from api.editais.router import router as editais_router
from api.checklist.router import router as checklist_router
from api.documentos.router import router as documentos_router
from api.alertas.router import router as alertas_router
from api.historico.router import router as historico_router
from api.lgpd.router import router as lgpd_router
from api.analytics.router import router as analytics_router
from api.mcp.router import router as mcp_router
from api.chat.router import router as chat_router
from api.perfil.router import router as perfil_router
from api.config.router import router as config_router
from api.plano.router import router as plano_router
from api.middleware import configurar_middleware, SecurityHeadersMiddleware

_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8501"
)
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]


async def _mongodb_keepalive(db) -> None:
    """Pinga o MongoDB a cada 25 min para evitar auto-pause no Atlas M0."""
    while True:
        await asyncio.sleep(25 * 60)
        try:
            await db.command("ping")
            logger.debug("MongoDB keep-alive: ping OK.")
        except Exception as exc:
            logger.warning("MongoDB keep-alive: falha no ping — %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("LicitaME API iniciando — conectando ao MongoDB...")
    app.state.db = AsyncIOMotorClient(MONGODB_URI)[MONGODB_DB]
    logger.info("Conexão com MongoDB estabelecida. API pronta.")
    keepalive_task = asyncio.create_task(_mongodb_keepalive(app.state.db))

    # Consumer Kafka de alertas (opcional — ativo apenas com KAFKA_BOOTSTRAP_SERVERS)
    from kafka.consumer import iniciar_consumer_alertas
    kafka_task = await iniciar_consumer_alertas(app.state.db)

    yield

    keepalive_task.cancel()
    if kafka_task:
        kafka_task.cancel()
    app.state.db.client.close()
    logger.info("LicitaME API encerrada — conexão com MongoDB fechada.")


app = FastAPI(
    title="LicitaME API",
    version="1.0.0",
    description="""
API da plataforma **LicitaME** — apoio a **Microempreendedores Individuais (MEIs)**
para descobrir e participar de licitações públicas no Brasil.

Integra dados em tempo real do **Portal Nacional de Contratações Públicas (PNCP)**,
autenticação JWT, chatbot com IA generativa e conformidade LGPD.

---

## Base legal

| Norma | Relevância |
|-------|-----------|
| Lei 14.133/2021 | Nova Lei de Licitações — habilitação (Arts. 62–70), preferência ME/EPP |
| LC 123/2006, Art. 48 | Preferência a MEI/ME/EPP em licitações ≤ R$ 80.000 |
| LGPD (Lei 13.709/2018) | Proteção de dados pessoais dos usuários cadastrados |

---

## Como usar

1. **Registre-se** — `POST /auth/register`
2. **Faça login** — `POST /auth/login` → copie o `access_token`
3. Clique em **Authorize** (cadeado) e cole o token
4. Explore os módulos abaixo

---

## Módulos

### 🔐 Autenticação
Registro e login com JWT (HS256). Todas as demais rotas exigem token Bearer.

### 📄 Editais
Busca paginada de editais do PNCP com filtros por CNAE, valor máximo e região.
Flag `favoravel_mei` indica contratos dentro do limite de preferência (≤ R$ 80.000).

### ✅ Checklist
Verificação automática de habilitação baseada na Lei 14.133/2021, com controle de progresso por edital.

### 📁 Documentos
Upload e gestão de arquivos de habilitação por edital, armazenados via GridFS (MongoDB).

### 🔔 Alertas
Alertas automáticos para novos editais conforme critérios configurados pelo MEI.

### 📊 Histórico
Registro e consulta do histórico de participações, com resumo por status.

### 🛡️ LGPD
Endpoints de conformidade: exportação e exclusão completa dos dados do usuário.

### 📈 Analytics
Análises dos dados PNCP via MongoDB Aggregation — espelha o pipeline PySpark:
estatísticas de valores, top órgãos e contratos favoráveis ao MEI.

### 🤖 MCP
Ferramentas do servidor MCP expostas como endpoints REST, invocáveis via HTTP.

### 💬 Assistente
Chatbot **Léo** (Claude + tool calling) que consulta a base PNCP em tempo real
e responde perguntas sobre licitações, órgãos e oportunidades para MEIs.
""",
    contact={"name": "LicitaME", "email": "contato@licitame.com.br"},
    license_info={"name": "MIT"},
    openapi_tags=[
        {
            "name": "🔐 Autenticação",
            "description": "Registro e login de usuários. Retorna token JWT para uso nas demais rotas.",
        },
        {
            "name": "📄 Editais",
            "description": "Busca e visualização de editais do PNCP com filtros e paginação.",
        },
        {
            "name": "✅ Checklist",
            "description": "Checklist de habilitação baseado na Lei 14.133/2021.",
        },
        {
            "name": "📁 Documentos",
            "description": "Upload e gestão de documentos por edital (armazenamento via GridFS).",
        },
        {
            "name": "🔔 Alertas",
            "description": "Criação e gestão de alertas automáticos para novos editais.",
        },
        {
            "name": "📊 Histórico",
            "description": "Histórico de participações em licitações com resumo por status.",
        },
        {
            "name": "🛡️ LGPD",
            "description": "Conformidade com a LGPD: exportação e exclusão de dados pessoais.",
        },
        {
            "name": "📈 Analytics",
            "description": (
                "Análises dos dados PNCP com duas fontes:\n\n"
                "**Tempo real (MongoDB Aggregation):** `GET /analytics/estatisticas`, "
                "`GET /analytics/top-orgaos`, `GET /analytics/contratos-mei`.\n\n"
                "**Batch (PySpark):** `GET /analytics/spark` lê os CSVs gerados por "
                "`spark/pyspark_transform.py` e expõe totais, estatísticas MEI, histograma "
                "de buckets e top órgãos. `POST /analytics/executar-spark` dispara o pipeline "
                "em background."
            ),
        },
        {
            "name": "🤖 MCP",
            "description": (
                "Ferramentas MCP do projeto expostas como endpoints REST. "
                "Idênticas às registradas em `mcp_server/server.py`."
            ),
        },
        {
            "name": "💬 Assistente",
            "description": (
                "Chatbot Léo (Claude) integrado via tool calling. "
                "Consulta a base PNCP em tempo real para responder perguntas sobre licitações."
            ),
        },
        {
            "name": "⚙️ Sistema",
            "description": "Endpoints de infraestrutura e monitoramento.",
        },
    ],
    lifespan=lifespan,
)

configurar_middleware(app)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(editais_router)
app.include_router(checklist_router)
app.include_router(documentos_router)
app.include_router(alertas_router)
app.include_router(historico_router)
app.include_router(lgpd_router)
app.include_router(analytics_router)
app.include_router(mcp_router)
app.include_router(chat_router)
app.include_router(perfil_router)
app.include_router(config_router)
app.include_router(plano_router)


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "service": "LicitaME API", "version": "1.0.0"}


_CHAT_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "chat.html")
_DASHBOARD_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dashboard.html")
_MONITOR_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "monitor.html")


@app.get("/app", include_in_schema=False)
async def chat_app():
    """Serve o frontend do chatbot Léo."""
    return FileResponse(_CHAT_HTML, media_type="text/html")


@app.get("/dashboard", include_in_schema=False)
async def dashboard_app():
    """Serve o dashboard de analytics LicitaME."""
    return FileResponse(_DASHBOARD_HTML, media_type="text/html")


@app.get("/monitor", include_in_schema=False)
async def monitor_app():
    """Serve o monitor da pipeline Medallion."""
    return FileResponse(_MONITOR_HTML, media_type="text/html")
