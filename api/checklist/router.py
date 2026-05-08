from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from .schemas import ChecklistResponse, MarcarRequisito
from .service import obter_checklist, marcar_requisito
from api.dependencies import get_db, get_usuario_atual

router = APIRouter(prefix="/editais/{edital_id}/checklist", tags=["checklist"])


@router.get("", response_model=ChecklistResponse)
async def get_checklist(
    edital_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(get_usuario_atual),
):
    return await obter_checklist(edital_id, usuario, db)


@router.patch("", response_model=ChecklistResponse)
async def atualizar_requisito(
    edital_id: str,
    dados: MarcarRequisito,
    db: AsyncIOMotorDatabase = Depends(get_db),
    usuario: dict = Depends(get_usuario_atual),
):
    return await marcar_requisito(
        edital_id, dados.requisito_id, dados.concluido, dados.documento_id, usuario, db
    )
