from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from .schemas import PerfilResponse, PerfilUpdate
from .service import obter_perfil, atualizar_perfil
from api.dependencies import get_db, get_usuario_atual

router = APIRouter(prefix="/perfil", tags=["👤 Perfil"])


@router.get(
    "",
    response_model=PerfilResponse,
    summary="Ver perfil",
    description="Retorna os dados do usuário autenticado.",
)
async def ver_perfil(
    usuario: dict = Depends(get_usuario_atual),
):
    return await obter_perfil(usuario)


@router.patch(
    "",
    response_model=PerfilResponse,
    summary="Atualizar perfil",
    description="Atualiza nome, e-mail, CNPJ e/ou senha do usuário autenticado.",
)
async def editar_perfil(
    dados: PerfilUpdate,
    usuario: dict = Depends(get_usuario_atual),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await atualizar_perfil(db, usuario, dados.model_dump(exclude_none=True))
