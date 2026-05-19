from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import MONGODB_URI, MONGODB_DB
from api.auth.router import router as auth_router
from api.editais.router import router as editais_router
from api.checklist.router import router as checklist_router
from api.documentos.router import router as documentos_router
from api.alertas.router import router as alertas_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = AsyncIOMotorClient(MONGODB_URI)[MONGODB_DB]
    yield
    app.state.db.client.close()


app = FastAPI(
    title="API MEI Licitações",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(editais_router)
app.include_router(checklist_router)
app.include_router(documentos_router)
app.include_router(alertas_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
