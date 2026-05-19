from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from .schemas import ParticipacaoCriar, ParticipacaoResponse, ResumoResponse
from .service import registrar_participacao, listar_participacoes, obter_resumo
from api.dependencies import get_db, get_usuario_atual

router = APIRouter(prefix="/historico", tags=["historico"])


@router.post("", response_model=ParticipacaoResponse, status_code=201)
async def registrar(
    dados: ParticipacaoCriar,
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(get_usuario_atual),
):
    return await registrar_participacao(dados.model_dump(), usuario, db)


@router.get("", response_model=list[ParticipacaoResponse])
async def listar(
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(get_usuario_atual),
):
    return await listar_participacoes(usuario, db)


@router.get("/resumo", response_model=ResumoResponse)
async def resumo(
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(get_usuario_atual),
):
    return await obter_resumo(usuario, db)
