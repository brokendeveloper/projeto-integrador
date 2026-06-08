from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from .schemas import AlertaCriar, AlertaResponse
from .service import criar_alerta, listar_alertas, excluir_alerta
from api.dependencies import get_db, get_usuario_atual

router = APIRouter(prefix="/alertas", tags=["🔔 Alertas"])


@router.post("", response_model=AlertaResponse, status_code=201, summary="Criar alerta de edital")
async def criar(
    dados: AlertaCriar,
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(get_usuario_atual),
):
    return await criar_alerta(dados.model_dump(), usuario, db)


@router.get("", response_model=list[AlertaResponse], summary="Ver meus alertas")
async def listar(
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(get_usuario_atual),
):
    return await listar_alertas(usuario, db)


@router.delete("/{alerta_id}", status_code=204, summary="Remover alerta")
async def excluir(
    alerta_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(get_usuario_atual),
):
    await excluir_alerta(alerta_id, usuario, db)
