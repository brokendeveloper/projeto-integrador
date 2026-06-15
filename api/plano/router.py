from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from .schemas import PlanoResponse
from .service import obter_plano, simular_upgrade
from api.dependencies import get_db, get_usuario_atual

router = APIRouter(prefix="/plano", tags=["💎 Plano"])


@router.get(
    "",
    response_model=PlanoResponse,
    summary="Ver plano atual",
    description="Retorna informações do plano do usuário e comparativo com o próximo plano.",
)
async def ver_plano(
    usuario: dict = Depends(get_usuario_atual),
):
    return await obter_plano(usuario)


@router.post(
    "/upgrade",
    response_model=PlanoResponse,
    summary="Simular upgrade/downgrade",
    description="Alterna entre os planos free e premium (demonstração). Em produção, integraria com gateway de pagamento.",
)
async def alternar_plano(
    usuario: dict = Depends(get_usuario_atual),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await simular_upgrade(db, usuario)
