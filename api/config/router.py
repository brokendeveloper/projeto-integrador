from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from .schemas import ConfigResponse, ConfigUpdate
from .service import obter_config, atualizar_config
from api.dependencies import get_db, get_usuario_atual

router = APIRouter(prefix="/config", tags=["⚙️ Configurações"])


@router.get(
    "",
    response_model=ConfigResponse,
    summary="Ver preferências",
    description="Retorna as preferências de notificações do usuário.",
)
async def ver_config(
    usuario: dict = Depends(get_usuario_atual),
):
    return await obter_config(usuario)


@router.patch(
    "",
    response_model=ConfigResponse,
    summary="Atualizar preferências",
    description="Atualiza as preferências de notificações do usuário.",
)
async def salvar_config(
    dados: ConfigUpdate,
    usuario: dict = Depends(get_usuario_atual),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await atualizar_config(db, usuario, dados.model_dump(exclude_none=True))
